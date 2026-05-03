from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal, Sequence, TypeVar

from sqlalchemy import func, inspect
from sqlalchemy.sql.elements import ColumnElement
from sqlmodel import Session, SQLModel, select

ModelT = TypeVar("ModelT", bound=SQLModel)
UTC_NOW = lambda: datetime.now(timezone.utc)

DistanceMetric = Literal["cosine", "l2", "inner_product"]

def create_one(session: Session, obj_in: ModelT, commit: bool = True, refresh: bool = True) -> ModelT:
    """
    ### Create a new database object and add it to the session. \n
    **Parameters**: \n
    - `session`: The database session to use for the operation. \n
    - `obj_in`: The object to be created (an instance of a SQLModel subclass). \n
    - `commit`: Whether to commit the transaction after adding the object. Default is True. \n
    - `refresh`: Whether to refresh the object from the database after committing. Default is True. \n
    **Returns**: \n
    The created database object, potentially with updated fields (like auto-generated IDs) after refreshing.
    """
    session.add(obj_in)
    if commit:
        session.commit()
    if refresh:
        session.refresh(obj_in)
    return obj_in


def create_many(session: Session, objects: list[ModelT], commit: bool = True, refresh: bool = False) -> list[ModelT]:
    """
    ### Create multiple new database objects and add them to the session. \n
    **Parameters**: \n
    - `session`: The database session to use for the operation. \n
    - `objects`: A list of objects to be created (instances of SQLModel subclasses).
    - `commit`: Whether to commit the transaction after adding the objects. Default is True. \n
    - `refresh`: Whether to refresh the objects from the database after committing. Default is False (can be expensive for large batches). \n
    **Returns**: \n
    The list of created database objects, potentially with updated fields after refreshing (if `refresh` is True). 
    """
    session.add_all(objects)
    if commit:
        session.commit()
    if refresh:
        for obj in objects:
            session.refresh(obj)
    return objects


def get_by_id(session: Session, model: type[ModelT], item_id: Any) -> ModelT | None:
    primary_keys = inspect(model).primary_key
    if len(primary_keys) != 1:
        raise ValueError(f"{model.__name__} must have exactly one primary key for get_by_id().")
    pk_column = primary_keys[0]
    statement = select(model).where(pk_column == item_id)
    return session.exec(statement).first()


def get_one(session: Session, model: type[ModelT], **filters: Any) -> ModelT | None:
    statement = select(model)
    for field_name, field_value in filters.items():
        statement = statement.where(getattr(model, field_name) == field_value)
    return session.exec(statement).first()


def get_all(session: Session, model: type[ModelT], offset: int = 0, limit: int = 100) -> list[ModelT]:
    statement = select(model).offset(offset).limit(limit)
    return list(session.exec(statement).all())


def get_many(session: Session, model: type[ModelT], offset: int = 0, limit: int = 100, **filters: Any) -> list[ModelT]:
    statement = select(model)
    for field_name, field_value in filters.items():
        statement = statement.where(getattr(model, field_name) == field_value)
    statement = statement.offset(offset).limit(limit)
    return list(session.exec(statement).all())


def update_one(session: Session, db_obj: ModelT, obj_in: ModelT | dict[str, Any], commit: bool = True, refresh: bool = True) -> ModelT:
    if isinstance(obj_in, dict):
        update_data = obj_in
    else:
        update_data = obj_in.model_dump(exclude_unset=True)

    for field_name, field_value in update_data.items():
        setattr(db_obj, field_name, field_value)

    if hasattr(db_obj, "updated_at"):
        setattr(db_obj, "updated_at", UTC_NOW())

    session.add(db_obj)
    if commit:
        session.commit()
    if refresh:
        session.refresh(db_obj)
    return db_obj


def delete_one(session: Session, db_obj: ModelT, commit: bool = True) -> None:
    session.delete(db_obj)
    if commit:
        session.commit()


def delete_by_id(session: Session, model: type[ModelT], item_id: Any, commit: bool = True) -> bool:
    db_obj = get_by_id(session, model, item_id)
    if db_obj is None:
        return False
    delete_one(session, db_obj, commit=commit)
    return True


def set_embedding(
    session: Session,
    db_obj: ModelT,
    embedding: Sequence[float],
    embedding_field: str = "embedding",
    commit: bool = True,
    refresh: bool = True,
) -> ModelT:
    """
    ### Set the embedding for a database object.
    **Parameters**: \n
    - `session`: The database session to use for the operation. \n
    - `db_obj`: The database object (model instance) for which to set the embedding. \n
    - `embedding`: The embedding vector to set for the object. \n
    - `embedding_field`: The name of the field in the model that contains the embedding vector. Default is "embedding". \n
    - `commit`: Whether to commit the transaction after setting the embedding. Default is True. \n
    - `refresh`: Whether to refresh the object from the database after committing. Default is True. \n
    
    **Returns**: \n
    The updated database object with the new embedding set.
    """
    if not hasattr(db_obj, embedding_field):
        raise ValueError(f"{type(db_obj).__name__} has no '{embedding_field}' field.")

    setattr(db_obj, embedding_field, list(embedding))

    if hasattr(db_obj, "updated_at"):
        setattr(db_obj, "updated_at", UTC_NOW())

    session.add(db_obj)
    if commit:
        session.commit()
    if refresh:
        session.refresh(db_obj)
    return db_obj


def get_similar(
    session: Session,
    model: type[ModelT],
    query_embedding: Sequence[float],
    embedding_field: str = "embedding",
    metric: DistanceMetric = "cosine",
    top_k: int = 5,
    offset: int = 0,
    **filters: Any,
) -> list[tuple[ModelT, float]]:
    """
    ### Retrieve the most similar items based on their embeddings using the specified metric. \n
    **Parameters**: \n
    - `session`: The database session to use for the query. \n
    - `model`: The SQLModel class representing the database table to query. \n
    - `query_embedding`: The embedding vector to compare against the stored embeddings. \n
    - `embedding_field`: The name of the field in the model that contains the embedding vector. Default is "embedding". \n
    - `metric`: The metric to use for comparison. Can be "cosine", "l2", or "inner_product". Default is "cosine". \n
    - `top_k`: The number of most similar items to return. Default is 5. \n
    - `offset`: The number of similar items to skip before returning results (for pagination). Default is 0. \n
    - `filters`: Additional field-value pairs to filter the query (e.g., by user_id, session_id, etc.). \n
    
    **Returns**: \n
    A list of tuples, where each tuple contains a model instance and its corresponding similarity score to the query embedding. The list is sorted by similarity (most similar first).
    """
    if not hasattr(model, embedding_field):
        raise ValueError(f"{model.__name__} has no '{embedding_field}' field.")

    embedding_col = getattr(model, embedding_field)
    query_vector = list(query_embedding)

    if metric == "cosine":
        distance_expr: ColumnElement[float] = embedding_col.cosine_distance(query_vector)
        similarity_expr: ColumnElement[float] = (1.0 - distance_expr)
    elif metric == "l2":
        distance_expr = embedding_col.l2_distance(query_vector)
        similarity_expr = (1.0 / (1.0 + distance_expr))
    elif metric == "inner_product":
        distance_expr = embedding_col.max_inner_product(query_vector)
        similarity_expr = (-1 * distance_expr)
    else:
        raise ValueError(f"Unsupported metric '{metric}'.")

    statement = select(model, similarity_expr.label("similarity"))

    for field_name, field_value in filters.items():
        statement = statement.where(getattr(model, field_name) == field_value)

    # Skip rows where embedding is missing so distance operators are valid.
    statement = statement.where(embedding_col.is_not(None))
    statement = statement.where(func.vector_dims(embedding_col) == len(query_vector))
    
    # Sort by similarity (highest first) and apply pagination.
    statement = statement.order_by(similarity_expr.desc()).offset(offset).limit(top_k)

    rows = session.exec(statement).all()
    return [(row[0], float(row[1])) for row in rows]
