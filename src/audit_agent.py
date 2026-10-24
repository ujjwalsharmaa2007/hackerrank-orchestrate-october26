
import re
import unicodedata


def normalize_text(text):
    text = unicodedata.normalize("NFKD", text.lower())
    text = "".join(
        char for char in text
        if not unicodedata.combining(char)
    )
    return re.sub(r"\s+", " ", text).strip()


def detect_deletion_request(request_text):
    text = normalize_text(request_text)

    deletion_words = [
        "delete",
        "deleting",
        "deleted",
        "deletion",
        "remove",
        "removal",
        "erase",
        "erasure",
        "purge",
        "wipe",
        "eliminar",
        "eliminacion",
        "borrar",
        "suprimir",
        "suppression",
        "supprimer",
        "effacer",
        "supressao",
        "excluir",
        "apagar",
        "loschen",
        "削除",
        "消去",
    ]

    personal_data_words = [
        "account",
        "profile",
        "personal",
        "data",
        "information",
        "details",
        "record",
        "copy",
        "copies",
        "email",
        "search result",
        "export",
        "attachment",
        "document",
        "identifier",
        "cuenta",
        "datos",
        "compte",
        "donnees",
        "adresse",
        "conta",
        "dados",
        "konto",
        "アカウント",
        "メールアドレス",
        "個人情報",
    ]

    account_closure_phrases = [
        "close my account",
        "close this account",
        "close the account",
        "closed my account",
        "account closure",
        "terminate my account",
        "shut down my account",
    ]

    if any(
        phrase in text for phrase in account_closure_phrases
    ):
        return True

    verification_words = [
        "check",
        "verify",
        "confirm",
        "inspect",
        "review",
        "tell me whether",
    ]

    deletion_context = [
        "request failed",
        "deletion request",
        "account still existed",
        "profile is gone",
        "account is gone",
        "still exists",
        "still existed",
    ]

    if (
        any(word in text for word in verification_words)
        and any(phrase in text for phrase in deletion_context)
    ):
        return True

    has_deletion_word = any(
        word in text
        if any(ord(char) > 127 for char in word)
        else bool(
            re.search(
                r"\b" + re.escape(word) + r"\b",
                text
            )
        )
        for word in deletion_words
    )

    has_personal_data_word = any(
        phrase in text for phrase in personal_data_words
    )

    return has_deletion_word and has_personal_data_word


if __name__ == "__main__":
    examples = [
        "Please delete my account.",
        "Please remove my personal details.",
        "Quiero eliminar mi cuenta.",
        "Je demande la suppression de mon compte.",
        "Can you remove that search result too?",
        "このアカウントの削除を依頼します。",
        "What is your refund policy?",
    ]

    for example in examples:
        print(
            detect_deletion_request(example),
            "|",
            example
        )
