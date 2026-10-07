"""Portable evidence paths and publication checks; no personal path allowlist."""
from pathlib import Path
import re


HOME_PATH = re.compile(r"(?i)(?:[A-Z]:[\\/](?:Users|Documents and Settings)[\\/]|(?<![A-Za-z0-9_/])(?:file://)?/(?:Users|home)/)[A-Za-z0-9_.-]+[\\/][^\s\"'<>\r\n]+")
PRIVATE_CONTEXT = re.compile(
    r"(?i)<(?:send_user_message_question_reply|user_request|assistant_response)>|"
    r"(?:pedido|solicitação|autorização|feedback|retorno direto|decisão) (?:do|pelo) usuário|"
    r"(?:o usuário|usuário) (?:informou|respondeu|confirmou|autorizou|escolheu|observou|revisou|aceitou)|"
    r"h[e]lper.{0,30}(?:un[k]nown_error|deny.read.ACL)")
SECRET = re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|\b(?:ghp_|github_pat_)[A-Za-z0-9_]{20,}|\bAKIA[A-Z0-9]{16}\b")


def public_path(value):
    """Retain an installed/source distinction without publishing an account path."""
    text = str(value).replace('\\', '/')
    if '/site-packages/' in text:
        return '<environment>/site-packages/' + text.split('/site-packages/', 1)[1]
    if '/src/azimlib' in text:
        return '<checkout>/src/azimlib' + text.split('/src/azimlib', 1)[1]
    return '<local>/' + text.rstrip('/').rsplit('/', 1)[-1]


def sanitize_text(text):
    return HOME_PATH.sub(lambda match: public_path(match.group()), text)


def findings(data):
    try:
        text = data.decode('utf-8')
    except UnicodeDecodeError:
        return []
    # JSON string escaping must not hide a Windows home directory.
    candidates = (text, text.replace('\\\\', '\\'))
    found = []
    for kind, pattern in (('personal-home-path', HOME_PATH),
                          ('conversation-context', PRIVATE_CONTEXT),
                          ('credential-pattern', SECRET)):
        if any(pattern.search(candidate) for candidate in candidates):
            found.append(kind)
    return found
