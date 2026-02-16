# import enum
# import ipaddress
# from datetime import datetime, timedelta

# from sqlalchemy import Column, Integer, Unicode, UniqueConstraint, asc, desc, func
# from sqlalchemy.ext.asyncio import AsyncSession

# from cnaas_nac.models.groups import Group
# from cnaas_nac.models.nas import NasPort
# from cnaas_nac.models.oui import DeviceOui
# from cnaas_nac.models.radcheck import RadCheck
# from cnaas_nac.models.radreply import RadReply
# from cnaas_nac.models.raduserinfo import RadUserInfo
# from cnaas_nac.tools.ouis import ouis


# def get_users(db: AsyncSession, field=None, condition="", order="", when=None, client_type=None,
#               usernames_list=[], group=None):
#     result = []

#     if group is not None and group != "all":
#         groupdict = Group.get(group)[0]
#         field = groupdict["fieldname"]
#         condition = groupdict["condition"]

#     db_order = asc(RadCheck.username)
#     db_field = RadCheck.username
#     db_condition = "%{}%".format(condition.lower())
#     db_when = datetime.now() - timedelta(days=3650)

#     if when is not None:
#         when_dict = {
#             "hour": datetime.now() - timedelta(hours=1),
#             "day": datetime.now() - timedelta(days=1),
#             "week": datetime.now() - timedelta(days=7),
#             "month": datetime.now() - timedelta(days=31),
#             "year": datetime.now() - timedelta(days=365),
#             "all": datetime.now() - timedelta(days=3650)
#         }

#         if when not in when_dict:
#             db_when = datetime.now() - timedelta(days=3650)
#         db_when = when_dict[when]

#     if field is not None:
#         field_dict = {
#             "username": func.lower(RadCheck.username),
#             "vlan": func.lower(RadReply.value),
#             "nasip": func.lower(NasPort.nas_ip_address),
#             "nasport": func.lower(NasPort.nas_port_id),
#             "reason": func.lower(RadUserInfo.reason),
#             "comment": func.lower(RadUserInfo.comment)
#         }

#         if field not in field_dict:
#             return []
#         db_field = field_dict[field]

#     if order != "":
#         if "username" in order:
#             db_order = (
#                 desc(RadCheck.username) if order.startswith(
#                     "-") else asc(RadCheck.username)
#             )
#         elif "vlan" in order:
#             db_order = desc(RadReply.value) if order.startswith(
#                 "-") else asc(RadReply.value)
#         elif "reason" in order:
#             db_order = (
#                 desc(RadUserInfo.reason) if order.startswith(
#                     "-") else asc(RadUserInfo.reason)
#             )
#         elif "comment" in order:
#             db_order = (
#                 desc(RadUserInfo.authdate)
#                 if order.startswith("-")
#                 else asc(RadUserInfo.authdate)
#             )
#         else:
#             db_order = desc(RadCheck.username)

#     userinfos = RadUserInfo.get(usernames=usernames_list)

#     with sqla_session() as session:
#         res = (
#             session.query(RadCheck, RadReply, NasPort, RadUserInfo)
#             .filter(RadCheck.username == NasPort.username)
#             .filter(RadReply.username == RadCheck.username)
#             .filter(RadReply.attribute == "Tunnel-Private-Group-Id")
#             .filter(RadUserInfo.username == RadCheck.username)
#             .filter(db_field.like(db_condition))
#             .filter(RadUserInfo.authdate > db_when)
#             .order_by(db_order)
#             .all()
#         )

#         for user, reply, nas_port, userinfo in res:
#             if usernames_list != []:
#                 if RadCheck.username not in usernames_list:
#                     continue

#             res_dict = dict()
#             res_dict["username"] = RadCheck.username
#             res_dict["password"] = ""

#             if user.op == ":=":
#                 res_dict["active"] = True
#             else:
#                 res_dict["active"] = False
#             res_dict["vlan"] = reply.value
#             res_dict["nas_identifier"] = nas_port.nas_identifier
#             res_dict["nas_port_id"] = nas_port.nas_port_id
#             res_dict["nas_ip_address"] = nas_port.nas_ip_address
#             res_dict["calling_station_id"] = nas_port.calling_station_id
#             res_dict["called_station_id"] = nas_port.called_station_id
#             res_dict["comment"] = userinfos[RadCheck.username]["comment"]
#             res_dict["reason"] = userinfos[RadCheck.username]["reason"]
#             res_dict["access_start"] = userinfos[RadCheck.username]["access_start"]
#             res_dict["access_stop"] = userinfos[RadCheck.username]["access_stop"]
#             res_dict["access_restricted"] = userinfos[RadCheck.username]["access_restricted"]
#             res_dict["accepts"] = userinfos[RadCheck.username]["accepts"]
#             res_dict["rejects"] = userinfos[RadCheck.username]["rejects"]
#             res_dict["authdate"] = userinfos[RadCheck.username]["authdate"]

#             user_oui = RadCheck.username[:8]

#             try:
#                 res_dict["vendor"] = ouis[user_oui]
#             except KeyError:
#                 res_dict["vendor"] = ""

#             if "authdate" not in userinfos[RadCheck.username]:
#                 authdate = ""
#             else:
#                 authdate = str(userinfos[RadCheck.username]["authdate"])

#             res_dict["authdate"] = authdate
#             result.append(res_dict)

#     return result