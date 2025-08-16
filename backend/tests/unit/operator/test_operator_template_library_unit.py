import pytest

from app.operator.template_library import AutomationTemplateLibrary


@pytest.mark.asyncio
async def test_operator_get_template_success():
    lib = AutomationTemplateLibrary()
    tpl = await lib.get_template("contact_form_lead_generator")
    assert tpl["id"] == "contact_form_lead_generator"


@pytest.mark.asyncio
async def test_operator_get_template_not_found():
    lib = AutomationTemplateLibrary()
    with pytest.raises(KeyError):
        await lib.get_template("missing")


@pytest.mark.asyncio
async def test_operator_list_templates_by_category_memory():
    lib = AutomationTemplateLibrary()
    res = await lib.list_templates_by_category("lead_generation")
    assert any(t["id"] == "contact_form_lead_generator" for t in res)


@pytest.mark.asyncio
async def test_operator_categories_memory():
    lib = AutomationTemplateLibrary()
    cats = await lib.categories()
    # DB may be populated from other tests; assert baseline category and non-empty set
    assert "lead_generation" in cats
    assert isinstance(cats, list) and len(cats) > 0


