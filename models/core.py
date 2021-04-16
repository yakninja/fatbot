from sqlalchemy.exc import NoResultFound, IntegrityError

from models import User, UserProfile, FoodUnit, FoodLog, Food, Unit, FoodName


def get_food_by_name(db_session, locale, name):
    """
    :param db_session:
    :param locale:
    :param name:
    :return:
    """
    fn = db_session.query(FoodName).filter_by(
        language=locale, name=name).one()
    if not fn:
        raise NoResultFound
    return fn.food


def create_food(db_session, locale, name, calories, fat, carbs, protein):
    """
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


def log_food(db_session, user: User, food: Food, unit: Unit, qty: float) -> FoodLog:
    """
    :param db_session:
    :param user:
    :param food:
    :param unit:
    :param qty:
    :return:
    """
    food_unit = db_session.query(FoodUnit).filter_by(food_id=food.id,
                                                     unit_id=unit.id).first()
    multiplier = qty * food_unit.grams
    food_log = FoodLog(user_id=user.id, food_id=food.id,
                       unit_id=unit.id, qty="{:.2f}".format(qty),
                       calories="{:.2f}".format(food.calories * multiplier),
                       carbs="{:.2f}".format(food.carbs * multiplier),
                       fat="{:.2f}".format(food.fat * multiplier),
                       protein="{:.2f}".format(food.protein * multiplier)
                       )
    db_session.add(food_log)
    db_session.commit()
    return food_log


def get_or_create_user(db_session, telegram_id) -> User:
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
