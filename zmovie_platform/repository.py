from __future__ import annotations

import uuid
from typing import Any

from .models import CharacterBible, Project, RenderJob, Scene, Shot, utcnow
from .storage import connect, dumps, loads


def save_project(project: Project) -> Project:
    project.updated_at = utcnow()
    with connect() as conn:
        conn.execute(
            "INSERT INTO projects(id,owner,name,concept,genre,visual_style,aspect_ratio,target_duration_seconds,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?) "
            "ON CONFLICT(id) DO UPDATE SET owner=excluded.owner,name=excluded.name,concept=excluded.concept,genre=excluded.genre,visual_style=excluded.visual_style,aspect_ratio=excluded.aspect_ratio,target_duration_seconds=excluded.target_duration_seconds,updated_at=excluded.updated_at",
            (project.id, project.owner, project.name, project.concept, project.genre, project.visual_style, project.aspect_ratio, project.target_duration_seconds, project.created_at, project.updated_at),
        )
        conn.execute("DELETE FROM characters WHERE project_id=?", (project.id,))
        conn.execute("DELETE FROM scenes WHERE project_id=?", (project.id,))
        for char in project.characters:
            conn.execute("INSERT INTO characters(id,project_id,payload) VALUES(?,?,?)", (char.id, project.id, dumps(char.to_dict())))
        for scene in project.scenes:
            payload = scene.to_dict().copy()
            payload.pop("shots", None)
            conn.execute("INSERT INTO scenes(id,project_id,order_index,payload) VALUES(?,?,?,?)", (scene.id, project.id, scene.order_index, dumps(payload)))
            for shot in scene.shots:
                conn.execute("INSERT INTO shots(id,scene_id,project_id,order_index,payload) VALUES(?,?,?,?,?)", (shot.id, scene.id, project.id, shot.order_index, dumps(shot.to_dict())))
    return project


def _row_project(row: Any) -> Project:
    return Project(
        id=row["id"], name=row["name"], concept=row["concept"], genre=row["genre"], visual_style=row["visual_style"],
        aspect_ratio=row["aspect_ratio"], target_duration_seconds=row["target_duration_seconds"], owner=row["owner"],
        created_at=row["created_at"], updated_at=row["updated_at"],
    )


def get_project(project_id: str) -> Project | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()
        if row is None:
            return None
        project = _row_project(row)
        for item in conn.execute("SELECT payload FROM characters WHERE project_id=? ORDER BY id", (project_id,)).fetchall():
            project.characters.append(CharacterBible(**loads(item["payload"], {})))
        scene_rows = conn.execute("SELECT * FROM scenes WHERE project_id=? ORDER BY order_index", (project_id,)).fetchall()
        for scene_row in scene_rows:
            data = loads(scene_row["payload"], {})
            data["shots"] = []
            scene = Scene(**data)
            shot_rows = conn.execute("SELECT payload FROM shots WHERE scene_id=? ORDER BY order_index", (scene.id,)).fetchall()
            for shot_row in shot_rows:
                scene.shots.append(Shot(**loads(shot_row["payload"], {})))
            project.scenes.append(scene)
        return project


def list_projects(owner: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
    limit = max(1, min(limit, 500))
    with connect() as conn:
        if owner:
            rows = conn.execute("SELECT * FROM projects WHERE owner=? ORDER BY updated_at DESC LIMIT ?", (owner, limit)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM projects ORDER BY updated_at DESC LIMIT ?", (limit,)).fetchall()
        return [dict(row) for row in rows]


def delete_project(project_id: str) -> bool:
    with connect() as conn:
        cur = conn.execute("DELETE FROM projects WHERE id=?", (project_id,))
        return cur.rowcount > 0


def save_job(job: RenderJob) -> RenderJob:
    job.updated_at = utcnow()
    with connect() as conn:
        conn.execute(
            "INSERT INTO render_jobs(id,project_id,shot_id,provider,status,output_path,error,created_at,updated_at,metadata) VALUES(?,?,?,?,?,?,?,?,?,?) "
            "ON CONFLICT(id) DO UPDATE SET status=excluded.status,output_path=excluded.output_path,error=excluded.error,updated_at=excluded.updated_at,metadata=excluded.metadata",
            (job.id, job.project_id, job.shot_id, job.provider, job.status, job.output_path, job.error, job.created_at, job.updated_at, dumps(job.metadata)),
        )
    return job


def new_job(project_id: str, shot_id: str, provider: str, metadata: dict[str, Any] | None = None) -> RenderJob:
    return save_job(RenderJob(id=f"job_{uuid.uuid4().hex[:12]}", project_id=project_id, shot_id=shot_id, provider=provider, metadata=metadata or {}))


def list_jobs(project_id: str | None = None, limit: int = 200) -> list[dict[str, Any]]:
    with connect() as conn:
        if project_id:
            rows = conn.execute("SELECT * FROM render_jobs WHERE project_id=? ORDER BY created_at DESC LIMIT ?", (project_id, limit)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM render_jobs ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        result = []
        for row in rows:
            item = dict(row)
            item["metadata"] = loads(item.get("metadata"), {})
            result.append(item)
        return result


def get_job(job_id: str) -> RenderJob | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM render_jobs WHERE id=?", (job_id,)).fetchone()
        if row is None:
            return None
        return RenderJob(
            id=row["id"], project_id=row["project_id"], shot_id=row["shot_id"], provider=row["provider"], status=row["status"],
            output_path=row["output_path"], error=row["error"], created_at=row["created_at"], updated_at=row["updated_at"], metadata=loads(row["metadata"], {}),
        )


def find_shot(project: Project, shot_id: str) -> tuple[Scene, Shot] | None:
    for scene in project.scenes:
        for shot in scene.shots:
            if shot.id == shot_id:
                return scene, shot
    return None


def add_asset(project_id: str, kind: str, name: str, path: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    asset_id = f"asset_{uuid.uuid4().hex[:12]}"
    with connect() as conn:
        conn.execute("INSERT INTO assets(id,project_id,kind,name,path,metadata) VALUES(?,?,?,?,?,?)", (asset_id, project_id, kind, name, path, dumps(metadata or {})))
    return {"id": asset_id, "project_id": project_id, "kind": kind, "name": name, "path": path, "metadata": metadata or {}}


def list_assets(project_id: str, kind: str | None = None) -> list[dict[str, Any]]:
    with connect() as conn:
        if kind:
            rows = conn.execute("SELECT * FROM assets WHERE project_id=? AND kind=? ORDER BY created_at DESC", (project_id, kind)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM assets WHERE project_id=? ORDER BY created_at DESC", (project_id,)).fetchall()
        out = []
        for row in rows:
            item = dict(row)
            item["metadata"] = loads(item.get("metadata"), {})
            out.append(item)
        return out
