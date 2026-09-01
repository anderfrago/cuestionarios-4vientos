from .extensions import db
from .models import Aspect, Item


FIRST = {
    "Bienestar emocional": [
        "Poco interés en hacer las cosas", "Te has sentido decaído/a",
        "Has tenido dificultad para dormir o has dormido demasiado",
        "Te has sentido cansado/a o con poca energía", "Te has sentido mal contigo mismo/a",
        "Has tenido dificultad para concentrarte", "Te has sentido nervioso/a o muy alterado/a",
        "Me siento apoyado/a por mi familia"],
    "Autoconocimiento y relaciones": [
        "Me cuesta mucho hablar ante un grupo", "Me gusta asumir responsabilidades",
        "Me cuesta tomar decisiones", "Me enfado a menudo", "Me cuesta controlarme",
        "Expreso mi opinión cuando algo me preocupa", "Soy una persona empática",
        "Me resulta fácil relacionarme con los demás", "Prefiero trabajar en equipo",
        "Soy capaz de gestionar mis emociones"],
    "Aprendizaje y hábitos": [
        "Me distraigo en clase", "Me cuesta concentrarme al estudiar", "Me cuesta memorizar datos",
        "Me cuesta razonar y reflexionar", "Me organizo y planifico el tiempo de estudio",
        "Tengo hábitos de estudio adecuados", "Sé pedir ayuda cuando la necesito"],
}

SECOND = {
    "Bienestar emocional": FIRST["Bienestar emocional"],
    "Habilidades personales y sociales": FIRST["Autoconocimiento y relaciones"],
    "Necesidades percibidas": [
        "Identifico mis dificultades de visión o audición", "Puedo mantener la atención en clase",
        "Puedo concentrarme al estudiar", "Memorizo los datos que necesito",
        "Razono y reflexiono ante los problemas", "Trabajo de forma individual con autonomía",
        "Trabajo de forma constructiva en grupo", "Me relaciono bien con el profesorado",
        "Me relaciono bien con mis compañeros/as", "Comunico lo que necesito"],
}


def seed_questionnaires():
    if Aspect.query.count():
        return
    for level, groups in ((1, FIRST), (2, SECOND)):
        for aspect_order, (name, items) in enumerate(groups.items(), 1):
            aspect = Aspect(level=level, name=name, order=aspect_order)
            db.session.add(aspect)
            db.session.flush()
            for item_order, text in enumerate(items, 1):
                negative = any(word in text.lower() for word in ("cuesta", "distraigo", "enfado"))
                db.session.add(Item(aspect_id=aspect.id, text=text, order=item_order,
                                    reverse_scored=negative))
    db.session.commit()

