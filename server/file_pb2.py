# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: file.proto
# Protobuf Python Version: 5.28.1
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(
    _runtime_version.Domain.PUBLIC,
    5,
    28,
    1,
    '',
    'file.proto'
)
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\nfile.proto\x12\x08greeting\"\x1e\n\x0bPingMessage\x12\x0f\n\x07message\x18\x01 \x01(\t\"/\n\x0cLoginRequest\x12\r\n\x05\x65mail\x18\x01 \x01(\t\x12\x10\n\x08password\x18\x02 \x01(\t\"z\n\x0fRegisterRequest\x12\r\n\x05\x65mail\x18\x01 \x01(\t\x12\x10\n\x08password\x18\x02 \x01(\t\x12\x0e\n\x06ticker\x18\x03 \x01(\t\x12\x11\n\trequestID\x18\x04 \x01(\t\x12\x10\n\x08lowValue\x18\x05 \x01(\t\x12\x11\n\thighValue\x18\x06 \x01(\t\"?\n\x0bUserRequest\x12\r\n\x05\x65mail\x18\x01 \x01(\t\x12\x0e\n\x06ticker\x18\x02 \x01(\t\x12\x11\n\trequestID\x18\x03 \x01(\t\"\"\n\x11\x44\x65leteUserRequest\x12\r\n\x05\x65mail\x18\x01 \x01(\t\"\x1f\n\x0cUserResponse\x12\x0f\n\x07message\x18\x01 \x01(\t\"!\n\x10GetTickerRequest\x12\r\n\x05\x65mail\x18\x01 \x01(\t\"5\n\x16GetAvarageXDaysRequest\x12\x0c\n\x04\x64\x61ys\x18\x01 \x01(\t\x12\r\n\x05\x65mail\x18\x02 \x01(\t\"]\n\x14ModifyLowHighRequest\x12\r\n\x05\x65mail\x18\x01 \x01(\t\x12\x11\n\trequestID\x18\x02 \x01(\t\x12\x10\n\x08lowValue\x18\x03 \x01(\t\x12\x11\n\thighValue\x18\x04 \x01(\t\"\"\n\x11ThresholdsRequest\x12\r\n\x05\x65mail\x18\x01 \x01(\t2\xa2\x02\n\x0e\x43ommandService\x12\x41\n\nCreateUser\x12\x19.greeting.RegisterRequest\x1a\x16.greeting.UserResponse\"\x00\x12=\n\nUpdateUser\x12\x15.greeting.UserRequest\x1a\x16.greeting.UserResponse\"\x00\x12\x43\n\nDeleteUser\x12\x1b.greeting.DeleteUserRequest\x1a\x16.greeting.UserResponse\"\x00\x12I\n\rUpdateHighLow\x12\x1e.greeting.ModifyLowHighRequest\x1a\x16.greeting.UserResponse\"\x00\x32\xe5\x02\n\x0cQueryService\x12\x36\n\x04Ping\x12\x15.greeting.PingMessage\x1a\x15.greeting.PingMessage\"\x00\x12=\n\tLoginUser\x12\x16.greeting.LoginRequest\x1a\x16.greeting.UserResponse\"\x00\x12\x41\n\tGetTicker\x12\x1a.greeting.GetTickerRequest\x1a\x16.greeting.UserResponse\"\x00\x12T\n\x16GetAvaragePriceOfXDays\x12 .greeting.GetAvarageXDaysRequest\x1a\x16.greeting.UserResponse\"\x00\x12\x45\n\x0cGetTresholds\x12\x1b.greeting.ThresholdsRequest\x1a\x16.greeting.UserResponse\"\x00\x62\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'file_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  DESCRIPTOR._loaded_options = None
  _globals['_PINGMESSAGE']._serialized_start=24
  _globals['_PINGMESSAGE']._serialized_end=54
  _globals['_LOGINREQUEST']._serialized_start=56
  _globals['_LOGINREQUEST']._serialized_end=103
  _globals['_REGISTERREQUEST']._serialized_start=105
  _globals['_REGISTERREQUEST']._serialized_end=227
  _globals['_USERREQUEST']._serialized_start=229
  _globals['_USERREQUEST']._serialized_end=292
  _globals['_DELETEUSERREQUEST']._serialized_start=294
  _globals['_DELETEUSERREQUEST']._serialized_end=328
  _globals['_USERRESPONSE']._serialized_start=330
  _globals['_USERRESPONSE']._serialized_end=361
  _globals['_GETTICKERREQUEST']._serialized_start=363
  _globals['_GETTICKERREQUEST']._serialized_end=396
  _globals['_GETAVARAGEXDAYSREQUEST']._serialized_start=398
  _globals['_GETAVARAGEXDAYSREQUEST']._serialized_end=451
  _globals['_MODIFYLOWHIGHREQUEST']._serialized_start=453
  _globals['_MODIFYLOWHIGHREQUEST']._serialized_end=546
  _globals['_THRESHOLDSREQUEST']._serialized_start=548
  _globals['_THRESHOLDSREQUEST']._serialized_end=582
  _globals['_COMMANDSERVICE']._serialized_start=585
  _globals['_COMMANDSERVICE']._serialized_end=875
  _globals['_QUERYSERVICE']._serialized_start=878
  _globals['_QUERYSERVICE']._serialized_end=1235
# @@protoc_insertion_point(module_scope)
