from apiflask.validators import FileType, FileSize
from apiflask.fields import File
from marshmallow import Schema, fields


class KnowledgeBaseFile(Schema):
    filename = File(
        validate=[FileType([".txt", ".pdf", ".doc", ".docx"]), FileSize(max="30 MB")]
    )


class KnowledgeBaseResponse(Schema):
    filename = fields.Str(required=True)
    mime_type = fields.Str(required=True)
    size = fields.Int(required=True)
