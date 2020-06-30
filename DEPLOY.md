# Deploys

We run two parallel stacks, a staging stack and a production stack. New versions are automatically deployed to Staging on every commit as part of CI.

Note that you don't need to run database migrations manually for the Elastic Beanstalk environments. They happen automatically. See [this ebextension](https://github.com/COVID19Tracking/covid-publishing-api/blob/master/.ebextensions/00_post_migrate.config) for details.

## Pushing to production

Visit the [list of application versions](https://console.aws.amazon.com/elasticbeanstalk/home?region=us-east-1#/application/versions?applicationName=covid-publishing-api). Under the "Deployed to" column, you should see both `prod` and `stage` next to some version. Hopefully `stage` is at or ahead of `prod`! If staging looks good (TODO: Help define what this means), go ahead and hit the checkbox next to the staged version, open the "Actions" menu, select "Deploy" and deploy to prod. That will kick off the migration, and if successful, the `prod` indicator should move to align with `stage`.
