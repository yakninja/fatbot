from sqlalchemy import table, column, Integer, String, insert
from sqlalchemy.exc import NoResultFound, IntegrityError
from sqlalchemy.orm import Session

from exc import FoodNotFound, UnitNotFound, UnitNotDefined
from models import User, UserProfile, FoodUnit, FoodLog, Food, Unit, FoodName, UnitName


def create_default_units(session: Session):
    """
    Create default units: grams and pc. Used in migrations and tests
    :param session:
    :return:
    """
    unit = table('unit')
    unit_name = table(
        'unit_name',
        column('unit_id', Integer),
        column('name', String),
        column('language', String),
    )
    units = [
        {
            'ru': ['г', 'грамм', 'гр', 'грам', 'граммов'],
            'en': ['g', 'gram', 'gr', 'grams'],
        },
        {
            'ru': ['шт', 'штук', 'штука'],
            'en': ['pc', 'pcs'],
        }
    ]
    gram_unit_id = None
    pc_unit_id = None
    for u in units:
        unit_id = session.execute(
            insert(unit).values()
        ).lastrowid

        if gram_unit_id is None:
            gram_unit_id = unit_id
        else:
            pc_unit_id = unit_id

        for lang in u.keys():
            for name in u[lang]:
                session.execute(
                    insert(unit_name).values(
                        {
                            'unit_id': unit_id,
                            'name': name,
                            'language': lang
                        }
                    )
                )
    session.commit()
    return gram_unit_id, pc_unit_id


def get_gram_unit(db_session: Session) -> Unit:
    """
    Shorthand for getting a gram unit
    :param db_session:
    :return:
    """
    return db_session.query(UnitName).filter_by(language='en', name='g').one().unit


def get_food_by_name(db_session: Session, locale: str, name: str) -> Food:
    """
    :param db_session:
    :param locale:
    :param name:
    :return:
    """
    return db_session.query(FoodName).filter_by(language=locale, name=name).one().food


def get_or_create_user(db_session: Session, telegram_id) -> User:
    """

    :param db_session:
    :param telegram_id:
    :return:
    """
    user = db_session.query(User).filter_by(telegram_id=telegram_id).first()
    if not user:
        user = User(telegram_id=telegram_id)
        db_session.add(user)
        db_session.commit()
        # TODO: configure calories etc. See https://www.calculator.net/macro-calculator.html
        profile = UserProfile(user_id=user.id,
                              daily_calories=1538,
                              daily_carbs=205,
                              daily_fat=44,
                              daily_protein=94)
        db_session.add(profile)
        db_session.commit()
    return user


def create_unit(db_session: Session, locale: str, name: str) -> Unit:
    """

    :param db_session:
    :param locale:
    :param name:
    :return:
    """
    u = Unit()
    db_session.add(u)
    if db_session.query(UnitName).filter_by(
            language=locale, name=name).count() > 0:
        db_session.rollback()
        raise IntegrityError
    db_session.commit()  # flush?
    un = UnitName(unit_id=u.id, language=locale, name=name)
    db_session.add(un)
    db_session.commit()
    return u


def define_unit_for_food(db_session: Session, food: Food, unit: Unit, grams: float, is_default: bool) -> None:
    try:
        fu = db_session.query(FoodUnit).filter_by(food_id=food.id, unit_id=unit.id).one()
    except NoResultFound:
        fu = FoodUnit(food_id=food.id, unit_id=unit.id)
    fu.grams = grams
    fu.is_default = is_default
    db_session.add(fu)
    db_session.commit()  # flush?
    if fu.is_default:
        # remove default from other units
        db_session.execute("""UPDATE food_unit SET is_default = :false 
            WHERE food_id = :food_id AND unit_id <> :unit_id""",
                           {'false': False, 'food_id': food.id, 'unit_id': unit.id})
        db_session.commit()
    gram_unit = get_gram_unit(db_session)
    if unit.id != gram_unit.id:
        fu = db_session.query(FoodUnit).filter_by(food_id=food.id, unit_id=gram_unit.id).first()
        if not fu:
            # also add grams
            fu = FoodUnit(food_id=food.id, unit_id=gram_unit.id, is_default=False, grams=1)
            db_session.add(fu)
            db_session.commit()


def get_unit_by_name(db_session: Session, locale: str, name: str) -> Unit:
    """
    :param db_session:
    :param locale:
    :param name:
    :return:
    """
    return db_session.query(UnitName).filter_by(language=locale, name=name).one().unit


def log_food(db_session: Session, locale: str, user: User,
             food_name: str, unit_name: str, qty: float,
             date=None) -> FoodLog:
    """
    Adds a food log entry for user
    :param db_session:
    :param locale:
    :param user:
    :param food_name:
    :param unit_name:
    :param qty:
    :param date: default: today's date (UTC)
    :return: FoodLog created log record
    :raises: FoodNotFound if no food was found with food_name, locale
    :raises: UnitNotFound if no unit was found with unit_name, locale
    :raises: UnitNotDefined if unit was found but not defined for this food
    """
    try:
        food = get_food_by_name(db_session, locale, food_name)
    except NoResultFound:
        raise FoodNotFound

    try:
        unit = get_unit_by_name(db_session, locale, unit_name)
    except NoResultFound:
        raise UnitNotFound

    try:
        food_unit = db_session.query(FoodUnit).filter_by(
            food_id=food.id,
            unit_id=unit.id).one()
    except NoResultFound:
        raise UnitNotDefined

    multiplier = qty * food_unit.grams
    food_log = FoodLog(user_id=user.id, food_id=food.id,
                       unit_id=unit.id, qty=qty,
                       calories=food.calories * multiplier,
                       carbs=food.carbs * multiplier,
                       fat=food.fat * multiplier,
                       protein=food.protein * multiplier,
                       date=date)
    db_session.add(food_log)
    db_session.commit()
    return food_log


def create_food(db_session: Session, locale: str, name: str,
                calories: float, fat: float, carbs: float, protein: float) -> Food:
    """
    Creates food of given value per 1 gram

    :param db_session:
    :param locale:
    :param name:
    :param calories:
    :param fat:
    :param carbs:
    :param protein:
    :return:
    """
    f = Food(calories=calories, fat=fat, carbs=carbs, protein=protein)
    db_session.add(f)

    if db_session.query(FoodName).filter_by(
            language=locale, name=name).count() > 0:
        db_session.rollback()
        raise IntegrityError
    db_session.commit()  # flush?
    fn = FoodName(food_id=f.id, language=locale, name=name)
    db_session.add(fn)
    db_session.commit()
    return f
