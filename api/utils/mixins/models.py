from django.db import models


class UserMixin(models.Model):
    """
    An abstract base class model that adds user information on creation and update
    """

    created_by = models.ForeignKey(
        'users.User', editable=False, blank=True, null=True,
        on_delete=models.PROTECT, related_name='created_by_%(class)ss'
    )
    updated_by = models.ForeignKey(
        'users.User', editable=False, blank=True, null=True,
        on_delete=models.PROTECT, related_name='updated_by_%(class)ss')

    class Meta:
        abstract = True