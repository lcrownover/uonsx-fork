# NSX Firewall Naming Conventions

There are many components involved with the NSX Distributed Firewall.
If we can follow a consistent naming convention, we can leverage automation to handle much of the minutiae of firewall management.

## TLDR

We have lots of services, which means lots of rules.
We gotta devise a system-within-a-system to make stuff work while not being a pain in the ass.

`Member Group`

- prefix: `mem_`
- convention of `mem_group-service[-prod|-test]_DATA`

`Function Group`

- prefix `fn_`
- convention of `fn_service-source_DATA`

A Member Group means you're a member of a very specific group, usually all members of this group are identical.

A Function Group is a group you join to change your security posture.

## Groups

Groups are the most important piece of creating scalable firewall rules.
Group membership is determined by criteria that's defined on the group.

Examples:

- VirtualMachine Tag EQUALS some-tag
- VirtualMachine OSName STARTSWITH "Ubuntu Linux"
- IP is x.x.x.x/x

In most cases, a group will be used with `VirtualMachine Tag EQUALS name-of-group`.
This means that if a VM object is tagged with `name-of-group`, it will be a member of that group.

To meet our scale and flexibility requirements, we have created two *types* of groups, a **Member Group** (`mem_`), and a **Function Group** (`fn_`).

While the two group types are technically the same, they serve distinct functional purposes.

### Member Group

A **Member Group** is a group that describes a single service.
This service would either be a single VM, or a cluster of VMs that are the same.
The same, meaning, each member of the group would have the *same* firewall rules.
You would typically only tag a VM with these tags during provisioning time, or when stakeholders add cluster members.

Using the Drupal Hosting service as an example:

```
is-drupal-hosting-mgmt-prod1  == tagged ==>  `mem_mad-drupal-hosting-mgmt_DATA`
is-drupal-hosting-log-prod1   == tagged ==>  `mem_mad-drupal-hosting-log_DATA`
is-drupal-hosting-web-prod1   == tagged ==>  `mem_mad-drupal-hosting-web_DATA`
is-drupal-hosting-web-prod2   == tagged ==>  `mem_mad-drupal-hosting-web_DATA`
is-drupal-hosting-web-prod3   == tagged ==>  `mem_mad-drupal-hosting-web_DATA`
```

Even though all these systems are part of the "drupal hosting" service, the **Member Group** would be more specific, at the *system purpose* level.
It will be very common to have **Member Group**s that only have a single VM. **This is by design**, as policies and rules deal with Groups, not VMs.

### Function Group

A **Function Group** is a group that provides common functionality to all members of the group.
An example of an function group is the group `fn_web-campus_DATA`. This group is mapped (by convention) to a policy, which contains a single rule.
The source of that rule is the `mem_campus_DATA` group, which is a list of all IP addresses for what we consider "campus networks".
The destination of that rule is the `fn_web-campus_DATA` group.
The policies associated with these groups typically only have one rule, as to favor composition via tags.

Using this convention, you would tag your VM with the `fn_web-campus_DATA` tag, and that's all you need to allow all web traffic from campus.

### Group Naming Convention

#### **Member Group** convention

`mem_service[-prod|test]_VRF`

Example:

`mem_banner-web-prod_DATA`

```
mem           Defining this group as a Member Group
banner-web    Service name. This can be anything, but typically what we'd see in the hostnames.
prod          Optional: If test and prod systems need different rulesets, we can append `prod` or `test` to have two groups.
VCF          VRF for this group. Most will be in DATA.
```

Other examples:

`mem_daisy_DATA`: Daisy cluster owned by the DBA group. No test/prod needed.

`mem_satellite_DATA`: Satellite hosts owned by systems.

`mem_f5-snat-addresses_DATA`: f5 SNAT IPs.

#### **Function Group** convention

`fn_web-campus_DATA`

```
fn          Defining this group as a Function Group
web         The service that this rule exposes
campus      The source of the traffic
DATA        VRF for this group. Most will be in DATA.
```

Other examples:

`fn_mgmt-adminvpn_DATA`: Allow management traffic (SSH, RDP, and WinRM) from admin vpn.

`fn_web-f5-snat_DATA`: Allow web traffic from the f5 SNAT IPs.

`fn_is-managed_DATA`: A unique group that contains all IS-Managed machines, used to implement what we know today as the "systems default rules".

## Policies

Policies are basically just containers for rules. Nothing else. Policies aren't applied, linked, or otherwise used. The only thing that matters is the source and destination of the rules inside a policy.

To make it easy to find rules associated with a **Member Group** or **Shared Policy**, we opt to name the policy the same as the group.
This helps with finding what rules are associated with what group when scrolling through the NSX UI.

An effect of these naming conventions, though, is that (for the vast majority of policies), the rules in a policy will all have their destination set to the same group that matches the name of the policy. **If you're ever modifying a policy where the destination group of a rule does not match the name of the policy, you should think twice**.

For example:

```
Policy:  mem_dba-daisy_DATA
Rules:

Source                     | Destination      | Service
--------------------------------------------------------
mem_daisy_DATA             | mem_daisy_DATA   | ANY
mem_banner-forms-prod_DATA | mem_daisy_DATA   | TCP_8109
mem_banner-web-prod_DATA   | mem_daisy_DATA   | HTTP, HTTPS


Policy:  fn_mgmt-adminvpn_DATA
Rules:

Source             | Destination           | Service
----------------------------------------------------
mem_admin-vpn_DATA | fn_mgmt-adminvpn_DATA | WinRM
mem_admin-vpn_DATA | fn_mgmt-adminvpn_DATA | RDP
mem_admin-vpn_DATA | fn_mgmt-adminvpn_DATA | SSH
```

### Proposed Policy Naming Convention

For the reasons stated above, it makes sense to name the policy the same as the group, as the destination for all the rules should be set to that group.

## Rules

Rule modifications are fairly straightforward if the above documentation makes sense. The name field is **not** used in any automation and is free to basically act as a `description` field.

Common things you might want to put in the name:

- TDX ticket #
- explaination of WHY the rule exists, if it seems odd
- a recipe for your favorite dish
