from rest_framework import serializers as ss


class NonEmptyCharField(ss.CharField):
    default_validators = [
        ss.validators.RegexValidator(
            regex=r'^\S+$',
            message='Поле не может быть пустым или содержать только пробелы'
        )
    ]
