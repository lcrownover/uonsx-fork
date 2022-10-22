# Migration

This document should outline the steps to migrate a VLAN from ACI to NSX.

- Creation of inter-vlan policy to allow L2 traffic
- Evaluation of Rules from ACI
- Creation of Member Group(s)
- Creation of Member Group Policy
- Creation of non-standard rules in Member Group Policy
- Recording of tags to use when VM is migrated


## Creation of L2 Adjacency member group for migrated networks

To replicate layer 2 networking as it is in ACI, we need to create a member group for each vlan.

For example, if you're just beginning to migrate VLAN 2742, you'd create a group/policy that contains a single rule:

`mem_vlan2742_DATA -> mem_vlan2742_DATA allow ALL`

You can create the group and policy separately, but we'll use the shorthand (you should too!):

```bash
uonsx policy create \
    --name "mem_vlan2742_DATA" \
    --category "Environment" \
    --create_group \
    --ip_address "163.41.192.8/29" \
    --owner "uo"
```

*You can set the owner to `uo` for these environment rules, there's not really an owner.*

Then we just add the single rule:

```bash
uonsx policy add-rule \
    --name "l2 allow" \
    --source_group "mem_vlan2742_DATA" \
    --service "ANY" \
    --policy_name "mem_vlan2742_DATA"
```

Once you've migrated all the VMs in the vlan, set the connected gateway to the T1 instead of ACI, and taken down the bridge from ACI, you'll want to remove the cidr from that group:

```bash
uonsx group remove-ipaddress \
    --name "mem_vlan2742_DATA" \
    --ip_address "ALL"
```


## Creation of Member Group(s)

For every cluster of VMs, create a member group, making sure to add the IP addresses of all cluster members.

A cluster is defined as a grouping of VMs where ALL firewall rules are the same.

```bash
uonsx group create \
    --name "mem_mysql-test_DATA" \
    --description "MySQL test cluster" \
    --ip_address "1.1.1.195,1.1.1.196" \
    --owner "dba"
```

`--ip_address`: You can use any number of comma-separated addresses that represents the cluster members. Do NOT use a network cidr here.

`--owner`: Typically, this will be which Puppet module the host belongs to. If it's not IS-Managed, use a good *lowercase* name that describes the **billing** owner of this service. This should not be a username, but rather a department.


## Tagging the VM for functionality via function groups

For a lot of virtual machines, they will have rules like "web from uonet". If the same exact rule could be used on 10+ systems, we should create a function group for that rule (if it doesn't already exist!)

```bash
uonsx policy create \
    --name "fn_web-uonet_DATA"
```

Then we add the single rule that this function group provides:

```bash
uonsx policy add-rule \
    --name "allow web from uonet" \
    --source_group "mem_uonet_DATA" \
    --service "ANY" \
    --policy_name "fn_web-uonet_DATA"
```

We can then tag the VM with that function group:

```bash
uonsx vm add-tag \
    --name "vmname" \
    --tag "fn_web-uonet_DATA"
```

*As we migrate more and more systems, function group creation should slow as we fill out the "catalog" of available function groups*


## Creation of Member Group Policy (if needed)

If the rules for a service are more unique than can be provided with simply tagging function groups, we need to create a Policy for the group.

```bash
uonsx policy create \
    --name "mem_mysql-test_DATA"
```


## Creation of non-function group rules in Member Group Policy

Any rule that cannot be provided by function groups should be added to the member group policy.

```bash
uonsx policy add-rule \
    --policy_name "mem_mysql-test_DATA" \
    --name "allow 8081 from something" \
    --source_group "mem_systems-mcafee_DATA" \
    --service "TCP_8081"
```


## Framework for Infrastructure, Environment, and Application

Decide on what rules will go into each section of the DFW.

- VLAN rules in infrastructure or env?
- IS-Managed in env? no ability to override in application firewall...
- fn rules in env or application?


## Process to move gateway

This process causes network disruption, probably schedule maintenance for critical stuff

1. Delete gateway in ACI -- wait for gateway to be gone
2. Add subnet and T1 to the NSX segment
