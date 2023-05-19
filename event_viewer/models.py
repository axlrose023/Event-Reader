from django.db import models


class EventLogReaderModel(models.Model):
    the_time = models.CharField(max_length=155, verbose_name='Час')
    etv_id = models.IntegerField(verbose_name='ID события')
    computer_name = models.CharField(max_length=155, verbose_name="Имя компьютера")
    user_name = models.CharField(max_length=155, verbose_name='Имя пользователя')
    category = models.CharField(max_length=155, verbose_name='Категория Логгов')
    source = models.CharField(max_length=155, verbose_name='Источник')
    record = models.CharField(max_length=155, verbose_name='Рекорд')
    event_type = models.CharField(max_length=155, verbose_name='Тип события')
    message = models.CharField(max_length=155, verbose_name='Сообщение')
    created_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f'ID события: {self.etv_id}, {self.event_type}'

    class Meta:
        verbose_name = "Event"
        verbose_name_plural = 'Events'



