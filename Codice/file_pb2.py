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




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\nfile.proto\x12\x08greeting\",\n\x0bUserRequest\x12\r\n\x05\x65mail\x18\x01 \x01(\t\x12\x0e\n\x06ticker\x18\x02 \x01(\t\"\"\n\x11\x44\x65leteUserRequest\x12\r\n\x05\x65mail\x18\x01 \x01(\t\"\x1f\n\x0cUserResponse\x12\x0f\n\x07message\x18\x01 \x01(\t\"!\n\x10GetTickerRequest\x12\r\n\x05\x65mail\x18\x01 \x01(\t2\x93\x02\n\x0bUserService\x12=\n\nCreateUser\x12\x15.greeting.UserRequest\x1a\x16.greeting.UserResponse\"\x00\x12=\n\nUpdateUser\x12\x15.greeting.UserRequest\x1a\x16.greeting.UserResponse\"\x00\x12\x43\n\nDeleteUser\x12\x1b.greeting.DeleteUserRequest\x1a\x16.greeting.UserResponse\"\x00\x12\x41\n\tGetTicker\x12\x1a.greeting.GetTickerRequest\x1a\x16.greeting.UserResponse\"\x00\x62\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'file_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  DESCRIPTOR._loaded_options = None
  _globals['_USERREQUEST']._serialized_start=24
  _globals['_USERREQUEST']._serialized_end=68
  _globals['_DELETEUSERREQUEST']._serialized_start=70
  _globals['_DELETEUSERREQUEST']._serialized_end=104
  _globals['_USERRESPONSE']._serialized_start=106
  _globals['_USERRESPONSE']._serialized_end=137
  _globals['_GETTICKERREQUEST']._serialized_start=139
  _globals['_GETTICKERREQUEST']._serialized_end=172
  _globals['_USERSERVICE']._serialized_start=175
  _globals['_USERSERVICE']._serialized_end=450
# @@protoc_insertion_point(module_scope)
