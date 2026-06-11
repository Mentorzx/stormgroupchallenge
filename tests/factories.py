from typing import Any


def hibp_breach(
    *,
    name: str = "Adobe",
    title: str | None = None,
    domain: str | None = "adobe.com",
    breach_date: str | None = "2013-10-04",
    added_date: str | None = "2013-12-04T00:00:00Z",
    modified_date: str | None = "2022-05-15T23:52:49Z",
    pwn_count: int = 152445165,
    data_classes: list[str] | None = None,
    is_verified: bool = True,
    is_fabricated: bool = False,
    is_sensitive: bool = False,
    is_retired: bool = False,
    is_spam_list: bool = False,
    is_malware: bool = False,
    **overrides: Any,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "Name": name,
        "Title": title or name,
        "Domain": domain,
        "BreachDate": breach_date,
        "AddedDate": added_date,
        "ModifiedDate": modified_date,
        "PwnCount": pwn_count,
        "Description": f"{name} description",
        "LogoPath": f"{name}.png",
        "DataClasses": data_classes
        if data_classes is not None
        else ["Email addresses", "Passwords"],
        "IsVerified": is_verified,
        "IsFabricated": is_fabricated,
        "IsSensitive": is_sensitive,
        "IsRetired": is_retired,
        "IsSpamList": is_spam_list,
        "IsMalware": is_malware,
    }
    payload.update(overrides)
    return payload
