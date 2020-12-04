import logging as lg
import email
import imaplib
import uuid
from hashlib import sha1


def get_IMAP(username: str, psswd: str,
             host: str = "imap.gmail.com",
             port: int = 993):
    lg.debug("Inside IMAP function")
    imap = imaplib.IMAP4_SSL(host, port)
    imap.login(username, psswd)
    return imap


def get_messages_nb(imap):
    _, messages = imap.select("INBOX")
    return int(messages[0])


def read_subject_mail(imap, nb_messages):
    data = {}
    # Iterating backwards to get from most recent to oldest email
    for i in range(nb_messages, 0, -1):
        _, msg = imap.fetch(str(i), "(RFC822)")
        for response in msg:
            h = sha1()
            cur_email = email.message_from_bytes(response[1])
            subj = cur_email["Subject"]
            height, weight = list(map(int, subj.split(",")))
            date = cur_email["Date"]
            sender = cur_email["From"]
            h.update((date + sender).encode())
            cur_uuid = str(uuid.uuid4())
            data[h.hexdigest] = {"uuid": cur_uuid,
                                 "heigth": height,
                                 "weight": weight}
    return data


def read_last_email(imap, nb_messages, hashes):
    _, msg = imap.fetch(str(nb_messages), "(RFC822)")
    for response in msg:
        h = sha1()
        cur_email = email.message_from_bytes(response[1])
        subj = cur_email["Subject"]
        height, weight = list(map(int, subj.split(",")))
        date = cur_email["Date"]
        sender = cur_email["From"]
        h.update((date + sender).encode())
        cur_uuid = str(uuid.uuid4())
        if h.hexdigest() not in hashes:
            return {"uuid": cur_uuid,
                    "height": height,
                    "weight": weight,
                    "hash": h.hexdigest()}
        else:
            return -1


