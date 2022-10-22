import json

import pytest
from uonsx.config import NSXConfig
from uonsx import NSX
from uonsx.unit.group import NSXGroup
from uonsx.manager.group import NSXGroupManager
from uonsx.unit.expression import NSXExpression


@pytest.fixture
def nsx():
    return NSX(
        server="mock_server",
        username="mock_username",
        password="mock_password",
        domain_id="mock_domain_id",
        debug_level=0,
        mock=True,
    )


@pytest.fixture
def cfg(nsx):
    return nsx.cfg


def test_cfg_fixture(cfg):
    assert cfg.username == "mock_username"


@pytest.fixture
def sample_raw_group():
    return json.loads(
        '{"expression": [{"member_type": "VirtualMachine", "key": "Tag", "operator": "EQUALS", "value": "|lcrown-web", "resource_type": "Condition", "id": "9441fc98-f9a5-4a6a-850b-ce9bb453f0b4", "path": "/infra/domains/default/groups/lcrown-web-group/condition-expressions/9441fc98-f9a5-4a6a-850b-ce9bb453f0b4", "relative_path": "9441fc98-f9a5-4a6a-850b-ce9bb453f0b4", "parent_path": "/infra/domains/default/groups/lcrown-web-group", "marked_for_delete": false, "overridden": false, "_protection": "NOT_PROTECTED"}], "extended_expression": [], "reference": false, "resource_type": "Group", "id": "lcrown-web-group", "display_name": "systems-lcrown-web", "description": "example setup for a web cluster", "path": "/infra/domains/default/groups/lcrown-web-group", "relative_path": "lcrown-web-group", "parent_path": "/infra/domains/default", "unique_id": "80a4b229-dbd5-4700-bac5-542d16503d51", "marked_for_delete": false, "overridden": false, "_create_user": "adm-lcrown@uoregon.edu", "_create_time": 1631297763205, "_last_modified_user": "adm-lcrown@uoregon.edu", "_last_modified_time": 1631648143326, "_system_owned": false, "_protection": "NOT_PROTECTED", "_revision": 2}'
    )


@pytest.fixture
def sample_group(sample_raw_group):
    return NSXGroup(data=sample_raw_group)


@pytest.fixture
def sample_expression():
    return NSXExpression(
        {
            "member_type": "VirtualMachine",
            "value": "webvm",
            "key": "Tag",
            "operator": "EQUALS",
            "resource_type": "Condition",
        }
    )


@pytest.fixture
def sample_ipaddress_expression():
    return NSXExpression(
        {
            "resource_type": "IPAddressExpression",
            "ip_addresses": ["1.1.0.0/16", "1.1.1.2"],
        }
    )

@pytest.fixture
def sample_ipaddress_expression2():
    return NSXExpression(
        {
            "resource_type": "IPAddressExpression",
            "ip_addresses": ["1.1.1.89"],
        }
    )


def test_group_new(sample_group):
    assert bool(sample_group) == True


def test_group_str(sample_group):
    assert str(sample_group) == "NSXGroup(name='systems-lcrown-web'...)"


def test_group_name(sample_group):
    assert sample_group.name() == "systems-lcrown-web"


def test_group_id(sample_group):
    assert sample_group.id() == "lcrown-web-group"


def test_group_path(sample_group):
    assert sample_group.path() == "/infra/domains/default/groups/lcrown-web-group"


def test_group_dump(sample_group, sample_raw_group):
    assert sample_group.dump() == sample_raw_group


def test_group_to_json(sample_group, sample_raw_group):
    assert sample_group.to_json() == json.dumps(sample_raw_group)


def test_group_add_valid_tag(sample_group):
    sample_group.add_tag(key="owner", value="systems")
    assert {"scope": "owner", "tag": "systems"} in sample_group.tags()


def test_group_add_half_tag(sample_group):
    sample_group.add_tag(key="", value="systems")
    assert {"scope": "", "tag": "systems"} in sample_group.tags()


def test_group_remove_valid_tag(sample_group):
    sample_group.add_tag(key="owner", value="systems")
    sample_group.add_tag(key="something", value="else")
    sample_group.remove_tag(key="something", value="else")
    assert {"scope": "owner", "tag": "systems"} in sample_group.tags()
    assert {"scope": "something", "tag": "else"} not in sample_group.tags()


def test_group_remove_half_tag(sample_group):
    sample_group.add_tag(key="owner", value="systems")
    sample_group.add_tag(key="", value="else")
    sample_group.remove_tag(key="", value="else")
    assert {"scope": "owner", "tag": "systems"} in sample_group.tags()
    assert {"scope": "something", "tag": "else"} not in sample_group.tags()


def test_group_add_expression(sample_group, sample_expression):
    assert len(sample_group.expression_list()) == 1
    sample_group._add_expression(sample_expression, "OR")
    el = sample_group.expression_list()
    assert len(el) == 3
    assert el[0].member_type() == "VirtualMachine"
    assert el[1].conjunction_operator() == "OR"
    assert el[2].member_type() == "VirtualMachine"


def test_group_multiple_expressions_and_no_ip_address_expression(
    sample_group, sample_expression
):
    assert sample_group._multiple_expressions_and_no_ip_address_expression() == False
    sample_group._add_expression(sample_expression, "OR")
    assert sample_group._multiple_expressions_and_no_ip_address_expression() == True


def test_group_get_ipaddress_expression(sample_group, sample_ipaddress_expression):
    assert sample_group._get_ipaddress_expression() is None
    sample_group._add_expression(sample_ipaddress_expression, "OR")
    assert sample_group._get_ipaddress_expression() is not None

def test_group_set_ipaddress_expression(sample_group, sample_ipaddress_expression, sample_ipaddress_expression2):
    sample_group._add_expression(sample_ipaddress_expression, "OR")
    assert "1.1.1.2" in sample_group._get_ipaddress_expression().ip_addresses()
    sample_group._set_ipaddress_expression(sample_ipaddress_expression2)
    assert "1.1.1.2" not in sample_group._get_ipaddress_expression().ip_addresses()
    assert "1.1.1.89" in sample_group._get_ipaddress_expression().ip_addresses()
