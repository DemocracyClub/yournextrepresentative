from django_webtest import WebTest


class DataTimelineHTMLAssertions(WebTest):
    """
    Assertions about the data timeline HTML shown on ballot pages.

    Useful to detect states of a ballot.
    """

    def assertDataTimelineShown(self, response):
        self.assertInHTML("<h3>Data Timeline</h3>", response.text)

    def assertDataTimelineNoResults(self, response):
        if response.context["ballot"].polls_closed:
            self.assertContains(
                response, """<strong>Winner(s) unknown</strong>:"""
            )
            self.assertInHTML("""Tell us who won!""", response.text)
        else:
            self.assertInHTML(
                """
                <div class="timeline_item">
                    <h4>Results recorded</h4>
                    <div class="status_not_started">
                        <strong>Waiting for election to happen</strong>
                    </div>
                </div>
            """,
                response.text,
            )

    def assertDataTimelineNoSOPN(self, response):
        self.assertInHTML(
            """
            <div class="timeline_item">
                <h4>Nomination documents uploaded</h4>
                <div class="status_not_started">
                    <strong>No "SOPNs" uploaded yet</strong>.
                </div>
            </div>
        """,
            response.text,
        )

    def assertDataTimelineNoLockSuggestions(self, response):
        self.assertInHTML(
            """
            <div class="timeline_item">
                <h4>Candidates verified and lock suggested</h4>
                <div class="status_not_started">
                    <strong>No lock suggestions</strong> 
                    Upload a document before suggesting locking
                </div>
            </div>
        """,
            response.text,
        )

    def assertDataTimelineNotLocked(self, response):
        self.assertInHTML(
            """
            <div class="timeline_item">
                <h4>Final verification and locked</h4>
                <div class="status_not_started">
                    <strong>Not verified or locked</strong>
                </div>
            </div>
        """,
            response.text,
        )

    def assertDataTimelineShowAddCandidateCTA(self, response):
        if not response.context["user"].is_authenticated:
            self.assertInHTML(
                """
                <a href="/accounts/login/?next=/elections/local.foo.bar.2019-08-03/" class="show-new-candidate-form button">
                    Sign in to add a new candidate
                </a>
                """,
                response.text,
            )

    def assertDataTimelineCandidateAddingInProgress(self, response):
        self.assertDataTimelineShown(response)
        self.assertInHTML(
            """
            <div class="timeline_item">
                <h4>Pre-nomination Candidates added</h4>
                <div class="status_in_progress">
                    <strong>In Progress</strong>: help by adding candidates
                </div>
            </div>
        """,
            response.text,
        )
        self.assertDataTimelineShowAddCandidateCTA(response)
        self.assertDataTimelineNoSOPN(response)
        self.assertDataTimelineNoLockSuggestions(response)
        self.assertDataTimelineNotLocked(response)
        self.assertDataTimelineNoResults(response)

    def assertDataTimelineHasResults(self, response):
        self.assertDataTimelineNoResults(response)
