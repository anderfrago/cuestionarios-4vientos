from .extensions import db
from .models import (Aspect, FormAspect, Item, Question, Questionnaire,
                     QuestionnaireVersion, QuestionOption, QuestionRow, now)


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
    if not Aspect.query.count():
        for level, groups in ((1, FIRST), (2, SECOND)):
            for aspect_order, (name, items) in enumerate(groups.items(), 1):
                aspect = Aspect(level=level, name=name, order=aspect_order)
                db.session.add(aspect)
                db.session.flush()
                for item_order, text in enumerate(items, 1):
                    negative = any(word in text.lower() for word in ("cuesta", "distraigo", "enfado"))
                    db.session.add(Item(aspect_id=aspect.id, text=text, order=item_order,
                                        reverse_scored=negative))
    if not Questionnaire.query.count():
        _seed_editable_forms()
    _seed_center_forms()
    db.session.commit()


CYCLES = ["FP Especial Auxiliar en Servicios Administrativos Generales",
    "Grado Medio Gestión Administrativa", "Grado Medio Actividades Comerciales",
    "Grado Medio Sistemas Microinformáticos y Redes", "Grado Superior Administración y Finanzas",
    "Grado Superior Comercio Internacional", "Grado Superior Gestión de Ventas y Espacios Comerciales",
    "Grado Superior Transporte y Logística A", "Grado Superior Transporte y Logística B",
    "Grado Superior Administración de Sistemas Informáticos en Red",
    "Grado Superior Desarrollo de Aplicaciones Multiplataforma", "Grado Básico"]
DIFFICULTIES = ["Tengo dificultades en la visión", "Tengo dificultades en la audición",
    "Tengo problemas motrices", "Me distraigo en clase", "Me cuesta concentrarme al estudiar",
    "Me cuesta memorizar datos", "Me cuesta razonar y reflexionar", "Dificultad en tareas manuales",
    "Dificultad en trabajos individuales", "Dificultad en trabajos grupales",
    "Dificultades de relación con profesorado", "Dificultades con compañeros/as",
    "Dificultades personales: ansiedad, tristeza...", "Dificultades de salud física",
    "Dificultades de comunicación con las personas", "Dificultades de lectura y escritura",
    "Dificultades de cálculo y matemáticas", "Otras"]
WELLBEING = ["Poco interés en hacer las cosas", "Te has sentido decaído/a",
    "Has tenido dificultad para quedarte o permanecer dormido/a o has dormido demasiado",
    "Te has sentido cansado/a o con poca energía", "Sin apetito o has comido en exceso",
    "Te has sentido mal contigo mismo/a", "Has tenido dificultad para concentrarte",
    "Pensamientos de que estaría mejor muerto/a o de lastimarte de alguna manera",
    "Te has sentido nervioso/a, ansioso/a o muy alterado/a", "Me siento apoyado/a por mi familia", "Otros"]
SOCIAL = ["Me cuesta mucho hablar ante un grupo", "Me gusta asumir responsabilidades",
    "Me cuesta tomar decisiones", "Me enfado a menudo", "Me cuesta controlarme",
    "A veces me gustaría dar mi opinión o quejarme pero me callo",
    "Soy una persona empática (entiendo y me pongo en el lugar de la otra persona)",
    "Me resulta fácil relacionarme con los demás", "Prefiero trabajar en equipo",
    "Soy capaz de gestionar mis emociones (enfado, frustración, etc.)"]
DAYS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]


def _question(aspect, title, qtype, options=None, rows=None, scored=True, required=True,
              other=False, critical=False, critical_min=None, order=1, help_text=""):
    q = Question(aspect_id=aspect.id, title=title, question_type=qtype, is_scored=scored,
        required=required, allow_other=other, is_critical=critical,
        critical_score_min=critical_min, order=order, help_text=help_text)
    db.session.add(q); db.session.flush()
    for index, option in enumerate(options or [], 1):
        label, score = option if isinstance(option, tuple) else (option, None)
        db.session.add(QuestionOption(question_id=q.id, label=label, value=str(index), score=score, order=index))
    for index, label in enumerate(rows or [], 1):
        db.session.add(QuestionRow(question_id=q.id, label=label, order=index))
    return q


def _seed_editable_forms():
    yes_no = [("Sí", 1), ("No", 0)]
    difficulties = [("Ninguna", 1), ("Pocas", 2), ("Bastantes", 3), ("Muchas", 4)]
    frequency = [("Ningún día", 0), ("Varios días", 1), ("Más de la mitad de los días", 2), ("Casi todos los días", 3)]
    describes = [("Me describe", 1), ("No me describe", 0)]
    minutes = [("0", 0), ("30", 1), ("60", 2), ("90", 3), ("120", 4)]
    for level in (1, 2):
        form = Questionnaire(name=f"Cuestionario inicial de {level}º", level=level,
            description="Formulario inicial editable de autopercepción")
        db.session.add(form); db.session.flush()
        version = QuestionnaireVersion(questionnaire_id=form.id, version=1, status="published", published_at=now())
        db.session.add(version); db.session.flush()
        context = FormAspect(version_id=version.id, name="Contexto", order=1)
        wellbeing = FormAspect(version_id=version.id, name="Bienestar emocional", order=2)
        social = FormAspect(version_id=version.id, name="Autoconocimiento y relaciones", order=3)
        habits = FormAspect(version_id=version.id, name="Hábitos de estudio", order=4)
        db.session.add_all([context, wellbeing, social, habits]); db.session.flush()
        position = 1
        if level == 1:
            _question(context, "¿Conoces la existencia de un servicio de orientación en Cuatrovientos?",
                      "yes_no", yes_no, scored=False, order=position); position += 1
        _question(context, "Señala el ciclo que estás estudiando", "select", CYCLES,
                  scored=False, order=position); position += 1
        _question(wellbeing, "¿Has consultado alguna vez en el último año con alguna persona profesional por un problema de salud mental?",
                  "yes_no", yes_no, scored=False, order=1)
        _question(wellbeing, "Dificultades y necesidades percibidas hasta ahora", "matrix",
                  difficulties, DIFFICULTIES, other=True, order=2)
        frequency_q = _question(wellbeing, "¿Desde que empezó el curso, con qué frecuencia has tenido dificultades debido a las siguientes cuestiones?",
                  "matrix", frequency, WELLBEING, other=True, order=3)
        # La fila de autolesión se separa como pregunta crítica para aplicar umbral y revisión.
        frequency_q.rows = [r for r in frequency_q.rows if not r.label.startswith("Pensamientos de que")]
        _question(wellbeing, "Pensamientos de que estaría mejor muerto/a o de lastimarte de alguna manera",
                  "radio", frequency, critical=True, critical_min=1, order=4)
        _question(social, "Señala qué frases te describen mejor y cuáles no tienen nada que ver contigo",
                  "matrix", describes, SOCIAL, order=1)
        _question(habits, "¿Cuántos minutos dedicas a estudiar al día?", "number_matrix",
                  minutes, DAYS, order=1)
        if level == 1:
            categories = ["A pesar de todo", "Ni con todo a favor", "Sí pero no aprendo", "Tarde y mal",
                "Carné falso", "Agradecidos", "Castigos y amenazas", "Exitosa mediana dotación", "Vividores"]
            _question(habits, "Señala a qué categoría de estudiante crees que perteneces",
                      "radio", categories, scored=False, other=True, order=2)


PRACTICE_CYCLES = [
    "TL OL-V - CS Transporte y Logística (Online - Virtual)",
    "TL - CS Transporte y Logística",
    "AF - CS Administración y Finanzas",
    "CI - CS Comercio Internacional",
    "GVEC - CS Gestión de Ventas y Espacios Comerciales",
    "DAM - CS Desarrollo Aplicaciones Multiplataforma",
    "ASIR - CS Administración Sistemas Informáticos",
    "GA - CM Gestión Administrativa",
    "AC - CM Actividades Comerciales",
    "SMR - CM Sistemas Microinformáticos y Redes",
    "GB - Grado Básico Servicios Comerciales",
    "CFP Especial - Auxiliar en Servicios Administrativos y Generales",
]
PRACTICE_STATUS = [
    "Exención / Convalidación", "Prácticas aquí", "Prácticas Erasmus", "Renunciar",
]
SATISFACTION_ROWS = [
    "Conocimientos", "Materiales y recursos", "Metodología", "Evaluación",
    "Relación con el/la profesor/a", "Tu implicación", "Explicación de la materia",
]
SATISFACTION_EXPLANATION = """Valora tu grado de satisfacción respecto a los módulos y al profesorado.
La escala es 1 = nada satisfecho y 10 = totalmente satisfecho. Utiliza NP cuando ese profesor o
profesora no te haya dado clase en el módulo. Ten en cuenta la cantidad y calidad de los conocimientos;
los materiales y recursos; la metodología; la claridad de la evaluación; la relación con el profesorado;
tu propia implicación; y el dominio y la explicación de la materia."""


def _published_form(name, level, description, aspect_name, aspect_description=""):
    if Questionnaire.query.filter_by(name=name).first():
        return None, None
    form = Questionnaire(name=name, level=level, description=description)
    db.session.add(form); db.session.flush()
    version = QuestionnaireVersion(questionnaire_id=form.id, version=1, status="published",
                                   published_at=now())
    db.session.add(version); db.session.flush()
    aspect = FormAspect(version_id=version.id, name=aspect_name, description=aspect_description,
                        order=1)
    db.session.add(aspect); db.session.flush()
    return form, aspect


def _seed_center_forms():
    _, practice = _published_form(
        "Ficha Alumnado Prácticas", 2,
        "Recogida de datos del alumnado y situación prevista para las prácticas.",
        "Datos para prácticas",
        "Completa los datos tal y como figuran en tu DNI, NIE o pasaporte.",
    )
    if practice:
        fields = [
            ("Nombre", "Indica el nombre tal y como figura en el DNI o pasaporte.", True),
            ("1º Apellido", "Indica el primer apellido tal y como figura en el DNI o pasaporte.", True),
            ("2º Apellido", "Indica el segundo apellido tal y como figura en el DNI o pasaporte.", True),
            ("Nº NIF o NIE", "Número con letra mayúscula, sin puntos, espacios ni guiones. Ej.: 44687925Y. Si utilizas pasaporte, deja este campo vacío.", False),
            ("Nº Pasaporte", "Rellénalo si no has indicado NIF o NIE.", False),
            ("Móvil", "Sin espacios, comas ni caracteres especiales.", True),
            ("Email", "Correo del alumno/a. No se admiten direcciones @educacion.navarra.es.", True),
        ]
        for order, (title, help_text, required) in enumerate(fields, 1):
            _question(practice, title, "text", scored=False, required=required,
                      order=order, help_text=help_text)
        _question(practice, "Ciclo", "select", PRACTICE_CYCLES, scored=False, required=True,
                  order=8, help_text="Indica el curso y ciclo que estás estudiando.")
        situation_help = ("Para solicitar exención debes acreditar un año de experiencia en el sector y "
            "entregar en Secretaría la vida laboral, el certificado de empresa y la solicitud de exención. "
            "Para renunciar, entrega en Secretaría la solicitud de renuncia.")
        _question(practice, "Situación prácticas", "radio", PRACTICE_STATUS, scored=False,
                  required=True, order=9, help_text=situation_help)

    satisfaction_options = [("NP", None)] + [(str(value), value) for value in range(1, 11)]
    for level in (1, 2):
        _, satisfaction = _published_form(
            f"Cuestionario de satisfacción de {level}º", level,
            "Plantilla editable para valorar los módulos y el profesorado del curso.",
            "Módulos del ciclo y profesorado", SATISFACTION_EXPLANATION,
        )
        if satisfaction:
            title = ("Iban Sarria - Administración de Sistemas Operativos"
                     if level == 2 else "[Docente] - [Módulo]")
            _question(satisfaction, title, "matrix", satisfaction_options,
                      SATISFACTION_ROWS, scored=True, required=True, order=1,
                      help_text="Selecciona una valoración para cada aspecto. Usa NP si no procede.")
