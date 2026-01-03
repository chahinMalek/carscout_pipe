from core.entities.run import Run
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
            status=orm.status,
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
            status=entity.status,
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
