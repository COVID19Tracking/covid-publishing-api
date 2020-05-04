import os
import pytest
from loguru import logger
from data_convert import encryption

def test_round_trip():

    pwd = "pwd123"
    msg = "Hello World"

    logger.info(f"message = {msg}")
    encrypted_msg = encryption.encrypt(pwd, msg)
    logger.info(f"encrypted message = {encrypted_msg}")

    msg2 = encryption.decrypt(pwd, encrypted_msg)
    logger.info(f"result = {msg}")

    assert(msg == msg2)

    encrypted_msg, key = encryption.encrypt_keyed(pwd, msg)
    logger.info(f"encrypted message = {encrypted_msg}")
    logger.info(f"message key = {key}")


    msg2 = encryption.decrypt_keyed(key, encrypted_msg)
    logger.info(f"result = {msg}")

    assert(msg == msg2)


@pytest.fixture
def test_file() -> str:
    with open("test.txt", "w") as f:
        f.write("This is a test")
    f.close()

    yield "test.txt"

    if os.path.isfile("test.txt"):
        os.remove("test.txt")
    if os.path.isfile("test_tmp.txt"):
        os.remove("test_tmp.txt")
    if os.path.isfile("test.txt.encrypted"):
        os.remove("test.txt.encrypted")

def test_access_encrypted_file(test_file):

    # confirm that inital read returns content
    tmp_name = encryption.access_encrypted_file("key", "test.txt")
    assert(tmp_name == "test_tmp.txt")

    # confirm that file got encrypted
    with open("test_tmp.txt", "r") as f:
        raw = f.read()
    assert(raw == "This is a test")

    with open("test.txt.encrypted", "r") as f:
        raw = f.read()
    assert(raw != "This is a test")

    # confirm that clean deleteds temp file
    encryption.cleanup_encrypted_file("test.txt")
    assert(not os.path.exists("test_tmp.txt"))

    # confirm that 2nd read decrypts succesfull
    tmp_name = encryption.access_encrypted_file("key", "test.txt")
    assert(tmp_name == "test_tmp.txt")

    with open("test_tmp.txt", "r") as f:
        raw = f.read()
    assert(raw == "This is a test")

    encryption.cleanup_encrypted_file("test.txt")

    # confirm that bad filename fails
    with pytest.raises(Exception, match=r"Missing both .*"):
        encryption.access_encrypted_file("key", "test2.txt")

    # confirm that bad password fails
    with pytest.raises(Exception, match=r"Bad Password"):
        encryption.access_encrypted_file("keyx", "test.txt")
