from sqlalchemy import func, select

from core.entities.run import Run, RunStatus
from core.repositories.run_repository import RunRepository
from infra.db.models.run import RunModel
from infra.db.service import DatabaseService


class SqlAlchemyRunRepository(RunRepository):
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service

    def _convert_orm_to_entity(self, orm: RunModel) -> Run:
        return Run(
            id=orm.id,
            started_at=orm.started_at,
            status=RunStatus(orm.status),
            completed_at=orm.completed_at,
            listings_scraped=orm.listings_scraped,
            vehicles_scraped=orm.vehicles_scraped,
            errors_count=orm.errors_count,
            last_error_message=orm.last_error_message,
        )

    def _convert_entity_to_orm(self, entity: Run) -> RunModel:
        return RunModel(
            id=entity.id,
            started_at=entity.started_at,
            status=entity.status.value,
            completed_at=entity.completed_at,
            listings_scraped=entity.listings_scraped,
            vehicles_scraped=entity.vehicles_scraped,
            errors_count=entity.errors_count,
            last_error_message=entity.last_error_message,
        )

    def add(self, run: Run) -> Run:
        with self.db_service.create_session() as session:
            record = self._convert_entity_to_orm(run)
            session.add(record)
            session.commit()
            session.refresh(record)
            return self._convert_orm_to_entity(record)

    def update(self, run: Run) -> Run:
        with self.db_service.create_session() as session:
            record = session.get(RunModel, run.id)
            if record:
                record.status = run.status
                record.completed_at = run.completed_at
                record.listings_scraped = run.listings_scraped
                record.vehicles_scraped = run.vehicles_scraped
                record.errors_count = run.errors_count
                record.last_error_message = run.last_error_message
                session.commit()
                session.refresh(record)
                return self._convert_orm_to_entity(record)
            raise ValueError(f"Run with id {run.id} not found")

    def get(self, id: str) -> Run | None:
        with self.db_service.create_session() as session:
            result = session.get(RunModel, id)
            if result:
                return self._convert_orm_to_entity(result)
            return None

    def list_all(self, limit: int = 1000) -> list[Run]:
        with self.db_service.create_session() as session:
            query = select(RunModel).limit(limit)
            result = session.execute(query).scalars().all()
            return [self._convert_orm_to_entity(orm) for orm in result]

    def search(
        self,
        status: str | None = None,
        id_pattern: str | None = None,
        offset: int = 0,
        limit: int = 10,
    ) -> tuple[list[Run], int]:
        with self.db_service.create_session() as session:
            query = select(RunModel)

            if status:
                query = query.filter(RunModel.status == status)
            if id_pattern:
                query = query.filter(RunModel.id.like(f"%{id_pattern}%"))

            # Get total count before pagination
            count_query = select(func.count()).select_from(query.subquery())
            total_count = session.execute(count_query).scalar() or 0

            # Apply ordering and pagination
            query = query.order_by(RunModel.started_at.desc()).offset(offset).limit(limit)
            result = session.execute(query).scalars().all()

            entities = [self._convert_orm_to_entity(orm) for orm in result]
            return entities, total_count
