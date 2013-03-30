# coding: utf-8
import tornado.web


class CrudHandlerMetaclass(type):
    def __init__(cls, name, bases, attrs):
        result = super(CrudHandlerMetaclass, cls).__init__(name, bases, attrs)
        if attrs.get('__metaclass__') is not CrudHandlerMetaclass:
            if not cls.document:
                raise NotImplementedError('CrudHandler classes requires the field "document".')
            cls.query = cls.document.objects.all()
            cls.fields = cls.document._fields.keys()
            cls.exclude = []
            cls.template_path = cls.document.__name__.lower() + '/'
        else:
            cls.document = None
        return result


class CrudHandler(AccountsHandler):
    __metaclass__ = CrudHandlerMetaclass

    def obj(self, obj_id, fail_silently=False):
        try:
            return self.query.clone().get(pk=obj_id)
        except Exception as e:
            print e
            if fail_silently:
                return None
            self.raise404()

    def render(self, template_name, **kwargs):
        super(CrudHandler, self).render(self.template_path + template_name, **kwargs)

    def get_request_data(self):
        data = {}
        for arg in self.request.arguments.keys():
            data[arg] = self.get_argument(arg)
        return data

    def render_list(self, message=None):
        self.render('list.html', objs=self.query, message=message)

    def raise404(self):
        raise tornado.web.HTTPError(404, 'Object not found')

    def get(self, obj_id=None, edit=False):
        if self.request.uri.endswith('/new'):
            self.render('edit.html', obj=None)
        if obj_id:
            instance = self.obj(obj_id, fail_silently=True)
            if instance:
                if edit:
                    self.render('edit.html', obj=instance)
                else:
                    data = self.get_arguments('obj_data')
                    self.render('show.html', obj=instance)
            else:
                self.render_list('Object not found.')
        else:
            self.render_list()

    def put(self, obj_id):
        try:
            data = self.get_request_data()
            instance = self.obj(obj_id)
            instance.update(**data)
            self.render_list('Object updated successfully.')
        except ValidationError as e:
            # TODO: capture errors to send to form
            self.render('edit.html', obj=instance, errors=[], alert='Data sent contains some issues.')

    def post(self, obj_id=None, action=None):
        if obj_id and self.request.uri.endswith('/delete'):
            return self.delete(obj_id)
        if obj_id:
            return self.put(obj_id)
        try:
            data = self.get_request_data()
            instance = self.document(**data)
            instance.save()
            self.render_list('Object added successfully.')
        except ValidationError as e:
            # TODO: capture errors to send to form
            self.render('edit.html', obj=instance, errors=[], alert='Data sent contains some issues.')

    def delete(self, obj_id):
        instance = self.obj(obj_id)
        try:
            instance.delete()
            self.render_list('Object could not be deleted.')
        except:
            self.render_list('Object deleted successfully.')
