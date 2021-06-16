from datetime import datetime, timedelta


class BehaviorTestCaseMixin(object):
    def get_model(self):
        return getattr(self, "model")

    def create_instance(self, **kwargs):
        raise NotImplementedError("Implement me")


class DateframeableTests(BehaviorTestCaseMixin):
    """
    Dateframeable tests.

    Are dates valid? Are invalid dates blocked?
    Are querysets to filter past, present and future items correct?
    """

    def test_new_instance_has_valid_dates(self):
        """Test complete or incomplete dates,
        according to the "^[0-9]{4}(-[0-9]{2}){0,2}$" pattern (incomplete dates)"""
        obj = self.create_instance(start_date="2012-01")
        self.assertRegex(
            obj.start_date,
            "^[0-9]{4}(-[0-9]{2}){0,2}$",
            "date does not match pattern",
        )
        obj = self.create_instance(end_date="2012-02")
        self.assertRegex(
            obj.end_date,
            "^[0-9]{4}(-[0-9]{2}){0,2}$",
            "date does not match pattern",
        )

        obj = self.create_instance(start_date="2012-03")
        self.assertRegex(
            obj.start_date,
            "^[0-9]{4}(-[0-9]{2}){0,2}$",
            "date does not match pattern",
        )
        obj = self.create_instance(end_date="2012-04")
        self.assertRegex(
            obj.end_date,
            "^[0-9]{4}(-[0-9]{2}){0,2}$",
            "date does not match pattern",
        )

        obj = self.create_instance(start_date="2012-10-12")
        self.assertRegex(
            obj.start_date,
            "^[0-9]{4}(-[0-9]{2}){0,2}$",
            "date does not match pattern",
        )
        obj = self.create_instance(end_date="2012-12-10")
        self.assertRegex(
            obj.end_date,
            "^[0-9]{4}(-[0-9]{2}){0,2}$",
            "date does not match pattern",
        )

    def test_querysets_filters(self):
        """Test current, past and future querysets"""
        past_obj = self.create_instance(
            start_date=datetime.strftime(
                datetime.now() - timedelta(days=10), "%Y-%m-%d"
            ),
            end_date=datetime.strftime(
                datetime.now() - timedelta(days=5), "%Y-%m-%d"
            ),
        )
        current_obj = self.create_instance(
            start_date=datetime.strftime(
                datetime.now() - timedelta(days=5), "%Y-%m-%d"
            ),
            end_date=datetime.strftime(
                datetime.now() + timedelta(days=5), "%Y-%m-%d"
            ),
        )
        future_obj = self.create_instance(
            start_date=datetime.strftime(
                datetime.now() + timedelta(days=5), "%Y-%m-%d"
            ),
            end_date=datetime.strftime(
                datetime.now() + timedelta(days=10), "%Y-%m-%d"
            ),
        )

        self.assertEqual(
            self.get_model().objects.all().count(),
            3,
            "Something really bad is going on",
        )
        self.assertEqual(
            self.get_model().objects.past().count(),
            1,
            "One past object should have been fetched",
        )
        self.assertEqual(
            self.get_model().objects.current().count(),
            1,
            "One current object should have been fetched",
        )
        self.assertEqual(
            self.get_model().objects.future().count(),
            1,
            "One future object should have been fetched",
        )
