from j2subst import j2subst_function


@j2subst_function
def yummi() -> str:
    return "yummi"


@j2subst_function(alias="yummi_all_loud")
def yummi_uppercase() -> str:
    return yummi().upper()
