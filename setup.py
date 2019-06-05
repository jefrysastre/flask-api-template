from setuptools import setup

setup(name='FlaskAPI',
      version='1.0',
      description='Create web services using flask',
      url='None',
      author='Jefry Sastre',
      author_email='jefry.sastre@gmail.com',
      license='BSD',
      packages=['api'],
      install_requires=[
        'aniso8601==6.0.0',
        'Click==7.0',
        'Flask==1.0.2',
        'Flask-Cors==3.0.7',
        'Flask-HTTPAuth==3.2.4',
        'Flask-RESTful==0.3.7',
        'gunicorn==19.9.0',
        'httplib2==0.12.3'
        'itsdangerous==1.1.0'
        'Jinja2==2.10.1'
        'jsonpickle==0.9.5'
        'MarkupSafe==1.1.1'
        'peewee==3.9.3'
        'PyJWT==1.7.1'
        'PyMySQL==0.9.3'
        'pytz==2019.1'
        'six==1.12.0'
        'Werkzeug==0.14.1'
      ],
      zip_safe=False)
