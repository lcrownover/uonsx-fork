# uonsx

This module provides both a command-line tool and libraries to help automate NSX-T DFW.

Note: This is a fork of the actual repository taken on Saturday, October 22nd, 2022.
I've stripped all ip address information for obscurity.

## Important documents

See the [migration document](MIGRATION.md) for details about our migration process.

See the [naming document](NAMING.md) for naming conventions.

## Other Notes

### Services

Services for Rules can be either a `Service` or a `Raw-Port-Protocols`

If Raw:

- Service type [ TCP, UDP ]
- Source Ports []  # blank is ANY
- Destination Ports [ 22 ]

If Service:

- Name

### Creating a Service

We have two choices, we can create rules with raw ports, which is more straightforward,
or we can create Services to house the rules, essentially grouping them. This would be another
layer of grouping on top of Security Policies.

- Name
- Description
- Service Entries  # list of either other `Services` or `Port-Protocols`
    - If Port-Protocol:
        - Name
        - Type [ TCP, UDP ]
        - Source Ports []  # blank is ANY
        - Destination Ports [ 22 ]
    - If Service:  # used if you want an aggregate service
        - Name


## Quickstart

Summary of useful bits to get you started with the library

### Instatiate the main NSX object

```python
server = "nsx_server.example.org"
domain_id = "default"

username = "my_username"
password = "my_secure_password"

nsx = uonsx.NSX(
    server=server,
    domain_id=domain_id,
    username=username,
    password=password,
)
```

### Creating a new NSX Group

The first component in the NSX stack is the Group. The group acts as a dynamic container for virtual machines. The group is associated with a VM tag. There are two types of groups, similar to the two types of Security Policies (described below):

- Member Group

    - If the group is basically static, and you don't expect to be adding members to it, prefix the name with `mem_`.
    - When applying tags to systems to modify security posture, you will know to generally avoid `mem_` tags unless it's during provisioning.

- Function Group

    - If the group is a dynamic group that's used by some of the main policies, such as the `fn_web-campus` policy (associated with group `fn_web-campus`), prefix the name with `fn_`.
    - To apply function rules to a system, such as allowing web traffic from campus, you simply have to add the `fn_web-campus` tag to the system.
    - Since the tags are prefixed with `fn_`, you know you can safely add these tags without introducing unexpected behavior.

The gist is, if you're tagging systems to adjust security posture, any group that starts with `fn_` is designed for systems to be dynamically added, whereas groups with `mem_` are probably groups that you don't want your systems to be a part of.

Once we have a lot of our workloads migrated, creating new Function policies will be a fairly rare occurrence. Creating Service groups will happen all the time, as services are created across campus.


#### Basic

The easiest way is just to create the group, specifying only the `name` parameter:

```python
test_lcrown1_group = nsx.group.create("mem_lcrown-test")
```

This will create a new NSX Group object. The only criteria is that the VM must have a tag with the same name as the group. This is what we want most of the time, so it's the easy default.

#### Advanced

First, we need to create the expression that defines the group
We can use the `nsx.expression.tag()` method for an easy way to get an expression for a given tag name:

```python
expr_tag_test_lcrown = nsx.expression.tag("mem_lcrown-test")
```

Or, if we need to use some other critera like hostname, we can
use the `nsx.expression.new()` method to specify those options:

```python
expr_tag_test_lcrown = nsx.expression.new(
    member_type="virtualmachine", key="CompupterName", operator="equals", value="is-lcrown-rhel7"
)
```

Then we can create the group with the expression:

```python
test_lcrown1_group = nsx.group.create(name="mem_lcrown-test", expression=expr_tag_test_lcrown)
```

We can use multiple Expressions, but it gets a bit more complicated
as we have to introduce some logic operators

For example, say we want to add a system to a group, but it needs to be
both tagged with "is-managed", as well as being an Ubuntu server:

```python
expr_tag_is_managed = nsx.expression.new(
    member_type="virtualmachine",
    key="tag",
    operator="equals",
    value="fn_is-managed"
)
expr_os_is_ubuntu = nsx.expression.new(
    member_type="virtualmachine",
    key="osname",
    operator="STARTSWITH",
    value="Ubuntu Linux"
)
```

We can feed those expressions into the `create()` method, but you MUST
separate each expression with an AND or OR:

```python
AND = nsx.expression.AND
# OR = nsx.expression.OR

group = nsx.group.create(name="mem_lcrown-test", expression=[ expr_tag_is_managed, AND, expr_os_is_ubuntu ])
```


### Creating a new Security Policy

By convention, there are two kinds of security policies that we create.

- Function policies
    - Typically making use of `fn_` groups as destinations, these are policies like `fn_web-campus` (allow all web traffic from the campus IP blocks to anything tagged `fn_web-campus`), or `f5-snat-web-prod` (allow all web traffic from production f5 snat pool IPs to anything tagged `fn_f5-snat-web-prod`).
    - Name starts with `fn_` to easily differentiate between member groups.
    - Destinations for rules in a function policy are always `fn_` groups.

- Member policies
    - A list of rules that **all** apply to a single destination group (tagged `mem_`).
    - Created when some service needs a more unique configuration than what can be offered by the function policies.
    - For example, you need to allow 8443 from `mem_banner-forms-prod` to `mem_onbase-app`. You'd create an `mem_banner-forms-prod` policy, then add the rule:
        - Source: `mem_onbase-app`
        - Destination: `mem_banner-forms-prod`
        - Service: `TCP_8443`
        - Action: `ALLOW`
        - Applied To: [`mem_onbase-app`, `mem_banner-forms-prod`]

In our case, I'm going to want to add some rules that are unique to my service, so I need to create a new service policy:

```python
test_lcrown_policy = nsx.policy.create(name="mem_lcrown-test")
```


### Adding new rules to an existing Policy

Let's create a new rule on an existing policy.

We can create new rules for the policy with the `add_rule()` method
By default, it will add the rule to the end of the policy. You can
specify a `sequence_number` if you want to insert it between two rules

The `source_group` and `destination_group` parameters accept a single
`NSXGroup` object, or a list of `NSXGroup` objects, or the string `"ANY"`.

If `destination_group` is empty, it will use the parent group of the policy

The action parameter accepts a string from `[ALLOW, REJECT, DROP, JUMP_TO_APPLICATION`

The service parameter accepts a service or list of services from the Service objects in NSX. For most function services like HTTP, HTTPS, SSH, or RDP, you can just pass those names in.

You can also pass a raw port-protocol string instead of a service name.

Examples:

```
TCP_8443              -> TCP, source port any, destination port 8443
UDP_8443              -> UDP, source port any, destination port 8443
TCP_SRC_9000_DST_8443 -> TCP, source port 9000, destination port 844
```

Let's allow anything that's managed by IS to contact port 8443

```python
is_managed_group = nsx.group.get(name="fn_is-managed")

test_lcrown_policy.add_rule(
    name="8443 from is-managed",
    source_group=is_managed_group,
    service="TCP_8443",
    action="ALLOW",
)
```

Let's also allow the world to reach port 6789

```python
test_lcrown_policy.add_rule(
    name="6789 from any",
    source_group="ANY",
    service="TCP_6789",
    action="ALLOW",
)
```

### Tagging a Virtual Machine

The last piece we need is to actually tag a system with the specified tag.

Tags should be a 1-to-1 relationship with Groups, so if you apply the `fn_web-campus` tag to your VM, you should be able to assume that it's going to be a part of the `fn_web-campus` group. This means that any rules that have a source or destination of `fn_web-campus` will now affect your system.

To tag a system, get the system with `nsx.vm.get()` and add a tag to it using the `add_tag()` method:

```python
lcrown_test_vm = nsx.vm.get("is-lcrown-dev7")

lcrown_test_vm.add_tag("mem_lcrown-test")
```
