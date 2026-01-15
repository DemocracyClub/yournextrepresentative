GET {{host}}
HTTP 200
[Asserts]
xpath "string(//div[contains(@class, 'footer')]/div[contains(@class, 'container')])" matches "Dedicated to Mark Longair"
