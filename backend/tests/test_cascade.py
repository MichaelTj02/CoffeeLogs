from sqlalchemy import func, select

from app.models import Bean, BrewAttempt, BrewMethod


def count(db, model):
    return db.execute(select(func.count()).select_from(model)).scalar_one()


def test_deleting_a_bean_removes_methods_and_attempts(
    db, client, make_bean, make_method, make_attempt
):
    bean = make_bean()
    method = make_method(bean, name="V60")
    make_attempt(method)
    make_attempt(method, rating=5)

    assert client.delete(f"/beans/{bean.id}").status_code == 204

    db.expire_all()
    assert count(db, Bean) == 0
    assert count(db, BrewMethod) == 0
    assert count(db, BrewAttempt) == 0


def test_deleting_a_bean_leaves_other_beans_alone(
    db, client, make_bean, make_method, make_attempt
):
    doomed = make_bean(name="Doomed")
    survivor = make_bean(name="Survivor")
    make_attempt(make_method(doomed, name="V60"))
    kept_attempt = make_attempt(make_method(survivor, name="V60"))

    client.delete(f"/beans/{doomed.id}")

    db.expire_all()
    assert count(db, Bean) == 1
    assert count(db, BrewMethod) == 1
    assert db.execute(select(BrewAttempt.id)).scalars().all() == [kept_attempt.id]


def test_deleting_a_method_removes_its_attempts_only(
    db, client, make_bean, make_method, make_attempt
):
    bean = make_bean()
    doomed = make_method(bean, name="V60")
    sibling = make_method(bean, name="AeroPress")
    make_attempt(doomed)
    make_attempt(doomed)
    kept_attempt = make_attempt(sibling)

    assert client.delete(f"/methods/{doomed.id}").status_code == 204

    db.expire_all()
    assert count(db, Bean) == 1
    assert db.execute(select(BrewMethod.id)).scalars().all() == [sibling.id]
    assert db.execute(select(BrewAttempt.id)).scalars().all() == [kept_attempt.id]


def test_deleting_an_attempt_leaves_its_method_and_bean(
    db, client, make_bean, make_method, make_attempt
):
    method = make_method(make_bean(), name="V60")
    doomed = make_attempt(method)
    kept = make_attempt(method)

    client.delete(f"/attempts/{doomed.id}")

    db.expire_all()
    assert count(db, Bean) == 1
    assert count(db, BrewMethod) == 1
    assert db.execute(select(BrewAttempt.id)).scalars().all() == [kept.id]
