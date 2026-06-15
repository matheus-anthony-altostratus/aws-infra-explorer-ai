from models.infra_model import IAMRole, IAMGroup, IAMUser, IAMSummary

class IAMExtractor:

    _AWS_ROLE_PREFIXES = (
        "AWSServiceRole", "aws-", "AWS-", "OrganizationAccount",
        "AWSReserved", "StackSet-",
    )

    def __init__(self, session):
        self.iam = session.get_client("iam")

    def extract(self) -> IAMSummary:
        summary = IAMSummary()

        try:
            aliases = self.iam.list_account_aliases().get("AccountAliases", [])
            summary.account_alias = aliases[0] if aliases else ""
        except Exception:
            pass

        try:
            summary.users_count = self.iam.get_account_summary()\
                .get("SummaryMap", {}).get("Users", 0)
        except Exception:
            pass

        try:
            self.iam.get_account_password_policy()
            summary.password_policy = True
        except Exception:
            pass

        try:
            resp = self.iam.list_virtual_mfa_devices(AssignmentStatus="Assigned")
            summary.mfa_enabled = len(resp.get("VirtualMFADevices", [])) > 0
        except Exception:
            pass

        try:
            paginator = self.iam.get_paginator("list_roles")
            for page in paginator.paginate():
                for r in page["Roles"]:
                    name = r["RoleName"]
                    if any(name.startswith(p) for p in self._AWS_ROLE_PREFIXES):
                        continue
                    last_used = ""
                    try:
                        lu = r.get("RoleLastUsed", {})
                        if lu.get("LastUsedDate"):
                            last_used = lu["LastUsedDate"].strftime("%Y-%m-%d")
                    except Exception:
                        pass
                    policies = []
                    try:
                        ap = self.iam.list_attached_role_policies(RoleName=name)
                        policies = [p["PolicyName"] for p in ap.get("AttachedPolicies", [])]
                    except Exception:
                        pass
                    summary.roles.append(IAMRole(
                        resource_id       = r["Arn"],
                        name              = name,
                        description       = r.get("Description", ""),
                        created_at        = r["CreateDate"].strftime("%Y-%m-%d"),
                        last_used         = last_used,
                        attached_policies = policies,
                    ))
        except Exception:
            pass

        try:
            paginator = self.iam.get_paginator("list_groups")
            for page in paginator.paginate():
                for g in page["Groups"]:
                    name = g["GroupName"]
                    user_count = 0
                    try:
                        gd = self.iam.get_group(GroupName=name)
                        user_count = len(gd.get("Users", []))
                    except Exception:
                        pass
                    policies = []
                    try:
                        ap = self.iam.list_attached_group_policies(GroupName=name)
                        policies = [p["PolicyName"] for p in ap.get("AttachedPolicies", [])]
                    except Exception:
                        pass
                    summary.groups.append(IAMGroup(
                        resource_id       = g["Arn"],
                        name              = name,
                        user_count        = user_count,
                        attached_policies = policies,
                    ))
        except Exception:
            pass

        try:
            paginator = self.iam.get_paginator("list_users")
            for page in paginator.paginate():
                for u in page["Users"]:
                    raw_name = u["UserName"]
                    # Ocultar email — si el username tiene @ mostramos solo la parte local
                    username = raw_name.split("@")[0] if "@" in raw_name else raw_name

                    last_login = ""
                    try:
                        if u.get("PasswordLastUsed"):
                            last_login = u["PasswordLastUsed"].strftime("%Y-%m-%d")
                    except Exception:
                        pass

                    mfa_active = False
                    try:
                        mfa_resp = self.iam.list_mfa_devices(UserName=raw_name)
                        mfa_active = len(mfa_resp.get("MFADevices", [])) > 0
                    except Exception:
                        pass

                    policies = []
                    try:
                        ap = self.iam.list_attached_user_policies(UserName=raw_name)
                        policies = [p["PolicyName"] for p in ap.get("AttachedPolicies", [])]
                    except Exception:
                        pass

                    user_groups = []
                    try:
                        ug = self.iam.list_groups_for_user(UserName=raw_name)
                        user_groups = [g["GroupName"] for g in ug.get("Groups", [])]
                    except Exception:
                        pass

                    summary.users.append(IAMUser(
                        username          = username,
                        created_at        = u["CreateDate"].strftime("%Y-%m-%d"),
                        last_login        = last_login,
                        mfa_active        = mfa_active,
                        attached_policies = policies,
                        groups            = user_groups,
                    ))
        except Exception:
            pass

        return summary
