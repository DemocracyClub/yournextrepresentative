from django.forms import widgets


class DropAndPasteFileWidget(widgets.ClearableFileInput):
    template_name = "official_documents/sopn_upload_widget.html"

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["widget"]["attrs"].setdefault(
            "accept",
            ",".join(
                [
                    "application/pdf",
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    "image/png",
                    "image/jpeg",
                ]
            ),
        )
        return context
