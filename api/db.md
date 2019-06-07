

# App Configuration

    app = type('MetaApp', (object,), {
    'id': '',
    'name': "monitoramento",
    'mode': "server",
    'endpoint': "cloud.monitoramento.api",
    'host': "0.0.0.0",
    'port': 5010,
    'version': "1.0",
    'date_time_format': "%Y-%m-%d %H:%M:%S.%f",
    'base_url': "/api/v1.0/"
    })()

# Allow CORS

    CORS = True
    CORS_resources = {
        r"/api/*": {
            "origins": "*"
        }
    }

# DB Configuration

    db = MySQLDatabase(
    host="159.203.191.233",
    port=3306,
    database="monitoramento",
    user="iahealth",
    password="iahealth1234"
    )

    connection = connection.Connection(db)

    # Load models from db
    schema = Introspector.from_database(db)
    __models = schema.generate_models()

# Auth Configuration

    # Auth Config
    auth = type('MetaAuth', (object,), {})()
    
    auth.basic = Authorization.BasicAuth(
            resource=models.User,
            user_field=['name', 'email'],
            password_field=lambda item: item.password,
    )
    
    auth.token = Authorization.TokenAuth(
            resource=models.User,
            token_field='token',
            token_expiration_time=86400,
            date_time_format=app.date_time_format,
            secret_key="asdfa0sd9fqpoefkq2-faokw f-q24okfwaodfk sdf2",
    )

# Access_Level

    # AccessLevel Config
    access_level = type('MetaAuth', (object,), {
        # '__call__': lambda cls, user: user.access_level
        '__call__': lambda cls, user: 5
    })()

# Enable Login

    # Login Config
    login = type('MetaLogin', (object,), {
        "model": models.User,
        "auth": auth.basic,
        "services": auth.token.services,
        "token_field": "token",
        "expires_miliseconds": 86400,
        "date_time_format": app.date_time_format
    })()

# Enable File Download/ Upload

    # Files Download / Upload
    file_server = type('MetaFile', (object,), {
        "auth": auth.token,
        "allowed_extensions": ['png', 'jpg', 'jpeg', 'pdf'],
        "path": "data/",
        "access_level": {
            "GET": 10,
            "POST": 20
        }
        # "expires_miliseconds": 999999999
    })()

# Enable Logging

    # Logs Config
    logger = type('MetaLog', (object,), {
        "filename": 'logs/app',
        "when": 'midnight',
        "backupCount": 15,
        'level': logging.INFO
    })()
    

# Resources

Basic Resource Configuration

    {
        "model": models.Hospital,
        "auth": auth.token,
        "updated_at_field": "updated_at",
        "params": ["<int:id>"],
        "url": "hospital",
        "limit": 25,
        "filters": {
            "name": lambda query, value: query.where(models.Hospital.name.contains(value))
        },
        "access_level": {
            "GET": 0,
            "POST": 0,
            "PUT": 0,
            "DELETE": 0
        }
    },

More Complex Resource Select and Filter Configuration

    {
        "model": models.Internacoes,
        "params": ["<int:id>"],
        "url": "internacao",
        "limit": 25,
        "select": lambda _:
            models.Internacoes.select(
                models.Internacoes.id,
                models.Internacoes.braden,
                models.Internacoes.ransay,
                models.Internacoes.custo_unidade,
                models.Internacoes.custo_hospital,
                models.Internacoes.previsao_alta,

                models.User.id.alias("user_id"),
                models.User.name.alias("user_name"),

                models.Patient.id.alias("patient_id"),
                models.Patient.name.alias("patient_name"),

                models.Leito.id.alias("leito_id"),
                models.Leito.name.alias("leito_name"),

                models.Hospital.id.alias("hospital_id"),
                models.Hospital.name.alias("hospital_name"),

                models.Tuss.id.alias("tuss_id"),
                models.Tuss.name.alias("tuss_name"),
            )
            .join(models.User, on=(models.User.id == models.Internacoes.id_user))
            .join(models.Patient, on=(models.Patient.id == models.Internacoes.id_patient))
            .join(models.Leito, on=(models.Leito.id == models.Internacoes.id_leito))
            .join(models.Hospital, on=(models.Hospital.id == models.Leito.id_hospital))
            .join(models.Tuss, on=(models.Tuss.id == models.Internacoes.id_tuss)),
        "filters": {
            "user_name": lambda query, value: query.where(models.User.name.contains(value)),
            "patient_name": lambda query, value: query.where(models.Patient.name.contains(value)),
            "leito_name": lambda query, value: query.where(models.Patient.name.contains(value)),
            "cid_name": lambda query, value: query.where(models.Cid.name.contains(value)),
            "tuss_name": lambda query, value: query.where(models.Cid.name.contains(value)),
        }
    },

Basic Query Configuration:

    # get the cid table
    {
        "method": "GET",
        "url": "cid",
        "desc": "Get all the CID items",
        "auth": auth.token,
        "access_level": 10,
        "query": lambda **kwargs: models.Cid.select()
    },


# DB Schema 
    * COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    * COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
