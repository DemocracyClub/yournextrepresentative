{% load static %}

const pdfjs = await import('{% static "official_documents/js/pdf.mjs" %}');

pdfjs.GlobalWorkerOptions.workerSrc = '{% static "official_documents/js/pdf.worker.mjs" %}';

var SOPN_VIEWER = (function () {
    "use strict";

    var module = {};

    function drawRectangles(context, rectangles) {
        rectangles.forEach(rect => {
            context.beginPath();
            context.rect(rect.x, rect.y, rect.width, rect.height);
            context.lineWidth = rect.lineWidth || 1;
            context.strokeStyle = rect.color || 'red';
            context.stroke();
        });
    }

    function load_page(pdf, container, page_num, rectanglesPerPage) {
        return pdf.getPage(page_num).then(function (page) {

            var scale = 1.2;
            var page_container = document.createElement("div");
            var canvas = document.createElement("canvas");
            var viewport = page.getViewport({"scale": scale});

            page_container.className = "page_container";
            $(page_container).css({"position": "relative"});
            page_container.appendChild(canvas);
            if (canvas.getAttribute("data") !== "loaded") {
                canvas.setAttribute("data", "loaded");
                var context = canvas.getContext("2d");
                canvas.height = viewport.height;
                canvas.width = viewport.width;
                console.log(canvas.height)
                console.log(canvas.width)
                var renderContext = {
                    canvasContext: context,
                    viewport: viewport
                };

                var renderTask = page.render(renderContext);
                return renderTask.promise.then(function () {
                    container.append(page_container);

                    if (rectanglesPerPage && rectanglesPerPage[page_num]) {
                        drawRectangles(context, rectanglesPerPage[page_num]);
                    }


                    return page.getTextContent({normalizeWhitespace: true});
                }).then(function (textContent) {
                    var pdf_canvas = $(canvas),
                        page_text_layer = document.createElement("div");
                    page_text_layer.className = "text_layer";
                    page_container.appendChild(page_text_layer);
                    var canvas_offset_left = pdf_canvas.context.offsetLeft;
                    var canvas_offset_top = pdf_canvas.context.offsetTop;
                    var canvas_height = pdf_canvas.context.height;
                    var canvas_width = pdf_canvas.context.width;

                    $(page_text_layer).css({
                        left: canvas_offset_left + "px",
                        top: canvas_offset_top + "px",
                        height: canvas_height + "px",
                        width: canvas_width + "px"
                    });

                    pdfjs.renderTextLayer({
                        textContentSource: textContent,
                        container: page_text_layer,
                        viewport: viewport,
                        textDivs: []
                    });


                });

            }

        });
    }

    function ShowSOPNInline(sopn_url, ballot_paper_id, rectanglesPerPage) {
        // The container element
        var this_pdf_container = document.getElementById("sopn-" + ballot_paper_id);

        var loadingTask = pdfjs.getDocument(sopn_url);

        loadingTask.promise.then(function (pdf) {
            var promise = Promise.resolve();
            for (let page = 1; page <= pdf.numPages; page++) {
                promise = promise.then(() => load_page(pdf, this_pdf_container, page, rectanglesPerPage));
            }
            return promise;
        }).then(null, function (error) {

            if (error.name === "MissingPDFException") {
                this_pdf_container.innerHTML = "<h3>PDF file not found</h3>";
            }

            console.log(error);
        });

    }

    module.ShowSOPNInline = ShowSOPNInline;
    return module;
}());

export {SOPN_VIEWER};
