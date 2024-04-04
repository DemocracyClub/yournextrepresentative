var SOPN_VIEWER = (function () {
    "use strict";

    var module = {};

    function load_pages(pdf, container, page_num) {
        if (page_num > pdf.numPages) {
            return;
        }
        pdf.getPage(page_num).then(function (page) {

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
                var renderContext = {
                    canvasContext: context,
                    viewport: viewport
                };

                var renderTask = page.render(renderContext);
                renderTask.promise.then(function () {
                    container.append(page_container);
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

                    pdfjsLib.renderTextLayer({
                        textContentSource: textContent,
                        container: page_text_layer,
                        viewport: viewport,
                        textDivs: []
                    });
                });

            }

        });
        page_num++
        load_pages(pdf, container, page_num)
    }

    function show_google_viewer(sopn_url, container) {
        /*
        Show the Google document viewer if PDFJS can't deal with this document for whatever reason
        */
        var google_frame = document.createElement("iframe");
        google_frame.setAttribute("frameborder", 0);
        google_frame.setAttribute("allowfullscreen", true);
        google_frame.className = "document_viewer";
        var url = "https://docs.google.com/viewer?url=https://candidates.democracyclub.org.uk";
        url = url + encodeURI(sopn_url) + "&embedded=true";
        google_frame.setAttribute("src", url);
        container.append(google_frame);
    }

    function ShowSOPNInline(sopn_url, ballot_paper_id, options) {
        // The container element
        var this_pdf_container = document.getElementById("sopn-" + ballot_paper_id);

        try {
            var loadingTask = pdfjsLib.getDocument(sopn_url);

            loadingTask.promise.then(function (pdf) {
                load_pages(pdf, this_pdf_container, 1);

            }).then(null, function (error) {

                if (error.name === "MissingPDFException") {
                    this_pdf_container.innerHTML = "<h3>PDF file not found</h3>";
                }

                if (error.name === "InvalidPDFException") {
                    show_google_viewer(sopn_url, this_pdf_container);
                }
            });
        } catch (e) {
            show_google_viewer(sopn_url, this_pdf_container);
        }

    }

    module.ShowSOPNInline = ShowSOPNInline;
    return module;
}());
/* hoist SOPN_VIEWER into the global scope
   this allows us to minify it safely */
window.SOPN_VIEWER = SOPN_VIEWER;
