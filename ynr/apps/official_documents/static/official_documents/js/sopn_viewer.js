var SOPN_VIEWER = (function () {
    "use strict";

    var module = {};

    function load_pages_by_range(pdf, start_page, end_page) {
        if (start_page > pdf.numPages || start_page === end_page + 1) {
            return;
        }
        pdf.getPage(start_page).then(function (page) {

            var scale = 1.2;
            var page_container = document.createElement("div");
            var canvas = document.createElement("canvas");
            var viewport = page.getViewport(scale);

            page_container.className = "page_container";
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
                renderTask.then(function () {
                    window.pdf_container.append(page_container);
                    return page.getTextContent({normalizeWhitespace: true});
                }).then(function (textContent) {
                    var pdf_canvas = $(canvas),
                        page_text_layer = document.createElement("div");
                    page_text_layer.className = "text_layer";
                    page_container.appendChild(page_text_layer);

                    var canvas_offset = pdf_canvas.offset();
                    var canvas_height = pdf_canvas.get(0).height;
                    var canvas_width = pdf_canvas.get(0).width;

                    $(page_text_layer).css({
                        left: canvas_offset.left + "px",
                        top: canvas_offset.top + "px",
                        height: canvas_height + "px",
                        width: canvas_width + "px"
                    });

                    pdfjsLib.renderTextLayer({
                        textContent: textContent,
                        container: page_text_layer,
                        viewport: viewport,
                        textDivs: []
                    });
                    // Load more pages when this page is done
                    start_page++;
                    load_pages_by_range(pdf, start_page, end_page);
                });

            }

        });
    }
    function show_google_viewer(sopn_url) {
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
        window.pdf_container.append(google_frame);
    }

    function ShowSOPNInline(sopn_url, ballot_paper_id, options) {


        try {
            var loadingTask = pdfjsLib.getDocument(sopn_url);

            loadingTask.promise.then(function (pdf) {
                // The container element
                window.pdf_container = document.getElementById("sopn-" + ballot_paper_id);

                // Get the end page either from the defined range, or the total number of pages
                var start_page = options.start_page || 1;
                var end_page = options.end_page || pdf.numPages;
                load_pages_by_range(pdf, start_page, end_page);

            }).then(null, function (error) {
                window.pdf_container = document.getElementById("sopn-" + ballot_paper_id);
                if (error.name === "MissingPDFException") {
                    window.pdf_container.innerHTML = "<h3>PDF file not found</h3>";
                }

                if (error.name === "InvalidPDFException") {
                    show_google_viewer(sopn_url);
                }
            });
        } catch (e) {
            show_google_viewer(sopn_url);
        }

    }

    module.ShowSOPNInline = ShowSOPNInline;
    return module;
}());
/* hoist SOPN_VIEWER into the global scope
   this allows us to minify it safely */
window.SOPN_VIEWER = SOPN_VIEWER;
