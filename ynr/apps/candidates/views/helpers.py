class ProcessInlineFormsMixin:
    """
    A mixin class for `FormView` that handles inline formsets.


    To use:
    1. add `ProcessInlineFormsMixin` to your FormView class
    2. set `inline_formset_classes` to a dict containing the name of the
       inline formset you want in the template context and the inline formset
       class. You can also override `get_inline_formsets` with a method that
       returns a dict of the same structure.
    3. If your inline formsets require any kwargs when instantiated,
       override the `get_inline_formset_kwargs` method. This method will be
       called with the formset name (the key of the `inline_formset_classes`)
       and should return a dict with the kwargs for the form class.

    How it works:
    1. Each inline formset class in inline_formset_classes is instantiated with
       the kwargs returned by `get_inline_formset_kwargs`. They are bound to
       self.request.POST if the request method is POST.
    2. Each of these classes is added to the request context under the key used
       in`inline_formset_classes`.
    3. On POST to the view, `is_valid` is called on each inline formset, as well
       as the main `form` object.
    4. If all forms are valid, self.form_valid is called, with a dict of each
       form as the first argument. This is a breaking change from using the
       standard FormView that expects a single Form class.
    5. if not, self.form_invalid is called with a dict of all forms.

    """

    inline_formset_classes = {}

    def get_inline_formsets(self):
        return self.inline_formset_classes

    def get_inline_formset_kwargs(self, formset_name):
        return {}

    def get_inline_formset(self, formset_name):
        formset = self.get_inline_formsets()[formset_name]
        kwargs = self.get_inline_formset_kwargs(formset_name)
        if hasattr(self, "get_object"):
            kwargs["instance"] = self.object
        if self.request.method == "POST":
            return formset(self.request.POST, self.request.FILES, **kwargs)
        else:
            return formset(**kwargs)

    def get_all_initialized_inline_formsets(self):
        return {
            fs_name: self.get_inline_formset(fs_name)
            for fs_name in self.get_inline_formsets().keys()
        }

    def post(self, request, *args, **kwargs):
        """
        Handles POST requests, instantiating a form instance with the passed
        POST variables and then checked for validity.

        Copied from Django's `ProcessFormView`
        """

        if hasattr(self, "get_object"):
            self.object = self.get_object()
        form = self.get_form()
        all_forms = self.get_all_initialized_inline_formsets()
        all_forms["form"] = form
        all_valid = all([f.is_valid() for f in all_forms.values()])

        if all_valid:
            return self.form_valid(all_forms)
        else:
            return self.form_invalid(all_forms)

    def form_invalid(self, all_forms):
        """
        If the form is invalid, re-render the context data with the
        data-filled form and errors.
        """
        return self.render_to_response(self.get_context_data(**all_forms))

    def get_context_data(self, **kwargs):
        """
        Insert the formsets into the context dict.
        """
        for fs_name, fs in self.get_all_initialized_inline_formsets().items():
            if fs_name not in kwargs:
                kwargs[fs_name] = fs
        return super().get_context_data(**kwargs)
