import setuptools

setuptools.setup(
    name='turing-bot-client',
    version='0.0.2.post1',
    author='Simon Schmid',
    author_email='simon.schmid@scch.at',
    description='A small library to connect bots to the turing game',
    py_modules=['TuringBotClient'],
    install_requires=['pydantic']
)