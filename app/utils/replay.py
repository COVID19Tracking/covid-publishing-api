import base64
import csv
from datetime import datetime

import app.api.data

import io
import flask
import json
import numpy as np
import pandas as pd
import requests

from app import db
from app.models.data import Batch, CoreData, State


FILE_URL_PATTERN = 'https://raw.githubusercontent.com/COVID19Tracking/covid-tracking-data/{sha}/data/states_daily_4pm_et.csv'
LINK_URL_PATTERN = 'https://github.com/COVID19Tracking/covid-tracking-data/blob/{sha}/data/states_daily_4pm_et.csv'

GH_URL = 'https://api.github.com/repos/COVID19Tracking/covid-tracking-data/contents/data/states_daily_4pm_et.csv'


'''
Plan:
- Make a copy of "coreData" and "batches" tables.
- Trunc the tables
  truncate "coreData", batches;
- Reset the index (to -1000)
  ALTER SEQUENCE "batches_batchId_seq" MINVALUE -1000 RESTART WITH -1000;
- Run the code on all commits
  flask utils replay COMMITS_FILE 0 10
- insert copied tables onto "coreData" and "batches" tables


Prepare the DB:
- pg-dump data only:
  pg_dump -h 127.0.0.1 -p 5444 -U postgres -d data_production -t '"coreData"' -t batches -F c -Ox -a -f core_data_and_batches.dump
- pg-restore data only:
  pg_restore -h 127.0.0.1 -p 5444 -U ctp_stage -d data -F c -a -t batches -t coreData  core_data_and_batches.dump

- clear tables, for testing and such
  truncate "coreData", batches;

- Copy tables as quick backup/restore
  create table copy_core_data as table "coreData";
  create table copy_batches as table batches;

Funny commits:
- 8dbf0ceebdcc930e8c72bc97cfbe6dc30fe6563d
- 2344bd901b8c87675c35a611b193f6e61d65b1a6 added lastUpdateEt
'''


def _make_payload(core_data, sha):
    # TODO: make sure core data is the correct format

    if isinstance(core_data, pd.DataFrame):
        core_data = core_data.replace({np.nan: None}).to_dict(orient='records')

    rows = len(core_data)
    states = set([x['state'] for x in core_data])
    states = sorted(list(states))

    # make a reasonable heuristic here:
    if rows == 56 and len(states) == 56:
        data_entry_type = 'daily'
    else:
        data_entry_type = 'edit'

    batchNote = "Updating {} rows for {}".format(rows, ", ".join(states))

    request_data = {
        "context": {
            "dataEntryType": data_entry_type,
            "batchNote": batchNote,
            "shiftLead": "GitHub",
            "link": LINK_URL_PATTERN.format(sha=sha),
            },
        "coreData": core_data
    }

    return request_data


def _handle_data(data, date, sha):
    flask.current_app.logger.info("Handling commit " + sha)
    payload = _make_payload(data, sha=sha)
    res = app.api.data.post_core_data_json(payload)
    if res[1] > 202:
        flask.current_app.logger.error(res[1], res[0])
        return

    # update batch properties and publish
    batch_id = res[0].json['batch']['batchId']
    batch = Batch.query.get_or_404(batch_id)
    batch.isPublished = True
    batch.createdAt = date
    batch.publishedAt = date
    flask.current_app.logger.info("\tBatch {}, date {}".format(batch_id, date))
    db.session.add(batch)
    db.session.commit()


def _cleanup(df):
    ''' Remove stuff that are not part of coreData
    '''
    COLUMNS_TO_DROP = ['fips', 'hash', 'posNeg', 'totalTestResults',
                       'hospitalized', 'total']
    df = df.drop(columns=COLUMNS_TO_DROP, errors='ignore')

    # remove calculated columns
    incleased = [x for x in df.columns if x.find('Increase') > 0]
    df = df.drop(columns=incleased)

    # rename
    df = df.rename(columns={'lastUpdateEt': 'lastUpdateTime'})

    # clear negative values
    # known offenders:
    # - commit: 0a155b914252973aea1b7bb8254e272b64deb1ab, 20200320,NV,pending

    df_numeric = df._get_numeric_data()
    df_numeric[df_numeric < 0] = np.nan

    # drop duplicates
    df = df.drop_duplicates()

    return df


def _get_commit(commit_hash):
    '''
    returns (code, content)
    '''
    res = requests.get(GH_URL, {'ref': commit_hash})
    if res.status_code != 200:
        flask.current_app.logger.warning("" + str(res.status_code) + ": " + res.reason)
        return (res.status_code, None)

    j = res.json()
    if j['encoding'] != 'base64':
        # don't know what to do
        flask.current_app.logger.warning(
            "Unexpected encoding for %s: %s" % (commit_hash, j['encoding']))
        return (500, None)

    df = pd.read_csv(io.BytesIO(base64.b64decode(j['content'])))
    df = _cleanup(df)
    return (res.status_code, df)


def _find_diff(prev, current):
    if prev is None:
        # easy
        return current

    df = current.merge(
        prev, how = 'outer', indicator=True).loc[lambda x: x['_merge'] == 'left_only']
    # drop indicator
    df = df.drop(columns='_merge')
    return df


def replay(input_file, skip_first, first_line=None, step=None):
    logger = flask.current_app.logger
    if first_line is None:
        first_line = 0

    logger.info('Replaying batches from commits in %s, from line %d and step %r'
                % (input_file, first_line, step))

    # blow away all core data, states, batches
    #CoreData.query.delete()
    #State.query.delete()
    #Batch.query.delete()

    #db.session.commit()

    with open(input_file, newline='') as csvfile:
        commits = csv.DictReader(csvfile)
        prev = None
        commits = list(commits)
        for i, commit in enumerate(commits[first_line:first_line+step]):
            # 1. Log
            sha = commit['commit_hash']
            logger.debug("Handling commit %s" % sha)

            # 2. Handle commit
            status, df = _get_commit(sha)

            # we want to maintain the same order, so instead of skipping to the next
            # we're going to wait and retry
            # maybe not so much for the waiting
            if status != 200:
                status, df = _get_commit(sha)

            # send only changes
            diff = _find_diff(prev, df)
            if diff.empty:
                continue
            logger.info("{}. Commit {} with {} rows".format(i+first_line, sha, df.shape[0]))
            if i > 0 or (i == 0 and not skip_first):
                _handle_data(diff, commit['commit_date'], sha)
            prev = df

    logger.info('Replay complete!')
