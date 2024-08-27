import json, warnings
from db.db import db
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.inspection import inspect
from typing import Union, List, Optional


class BaseModel(db.Model):
    __abstract__ = True  # Indicates this is a base class, not a table

    @classmethod
    def get(
        cls, identifier: Union[int, dict, str]
    ) -> Optional[Union["BaseModel", List["BaseModel"]]]:
        query = db.session.query(cls)

        if isinstance(identifier, dict):
            query = cls._generate_filter(query, identifier, cls)
            return query.all()
        elif isinstance(identifier, int):
            return query.filter_by(id=identifier).first()
        else:
            return query.filter_by(sid=identifier).first()

    @classmethod
    def delete(cls, identifier: Union[int, dict, str]) -> bool:
        query = db.session.query(cls)

        if isinstance(identifier, dict):
            query = cls._generate_filter(query, identifier, cls)
        elif isinstance(identifier, int):
            query = query.filter_by(id=identifier)
        else:
            query = query.filter_by(sid=identifier)

        try:
            records = query.all()
            if records:
                for record in records:
                    db.session.delete(record)
                db.session.commit()
                return True
        except SQLAlchemyError as e:
            db.session.rollback()
            raise e

        return False

    @classmethod
    def insert(cls, obj) -> Optional[int]:
        columns = {
            column.name: (
                json.dumps(getattr(obj, column.name, None))
                if isinstance(getattr(obj, column.name), dict)
                else getattr(obj, column.name, None)
            )
            for column in inspect(cls).columns
            if hasattr(obj, column.name)
        }
        instance = cls(**columns)
        try:
            db.session.add(instance)
            db.session.commit()
            return instance.id
        except SQLAlchemyError as e:
            db.session.rollback()
            raise e

    @classmethod
    def update(cls, identifier: Union[int, dict, str], obj) -> Optional[int]:
        try:
            update_values = {
                column.name: (
                    json.dumps(getattr(obj, column.name, None))
                    if isinstance(getattr(obj, column.name), dict)
                    else getattr(obj, column.name, None)
                )
                for column in inspect(cls).columns
                if hasattr(obj, column.name)
            }

            query = db.session.query(cls)
            if isinstance(identifier, dict):
                query = query.filter_by(**identifier)
            elif isinstance(identifier, int):
                query = query.filter_by(id=identifier)
            else:
                query = query.filter_by(sid=identifier)

            affected_rows = query.update(update_values)
            db.session.commit()

            return affected_rows
        except SQLAlchemyError as e:
            db.session.rollback()
            raise e

    @classmethod
    def to_dict(
        cls, model_instances: Union["BaseModel", List["BaseModel"]]
    ) -> Union[dict, List[dict]]:
        # if isinstance(model_instances, list):
        return [
            cls._model_to_dict(model_instance) for model_instance in model_instances
        ]
        # return cls._model_to_dict(model_instances) if model_instances is not None else {}

    @classmethod
    def toDict(
        cls, model_instances: Union["BaseModel", List["BaseModel"]]
    ) -> Union[dict, List[dict]]:
        warnings.warn(
            "The method 'toDict' is deprecated. Please use 'to_dict' instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return cls.to_dict(model_instances)

    @staticmethod
    def _model_to_dict(model_instance) -> dict:
        """Convert a SQLAlchemy model instance to a dictionary."""
        if model_instance is None:
            return {}
        return {
            column.name: getattr(model_instance, column.name)
            for column in inspect(model_instance.__class__).columns
        }

    @staticmethod
    def _generate_filter(query, filters, model_class):
        for column, value in filters.items():
            if hasattr(model_class, column):
                query = query.filter(getattr(model_class, column) == value)
            else:
                raise AttributeError(
                    f"Column {column} does not exist in model {model_class.__name__}"
                )
        return query
