import App from './App.svelte'

var dummy_data = {
    sopn_pdf: "https://s3.eu-west-2.amazonaws.com/static-candidates.democracyclub.org.uk/media/official_documents/local.tandridge.2024-05-02/2024-04-05T18%3A23%3A03.267470%2B00%3A00/Statement_of_Persons_Nominated_Tandridge_District_2024.pdf",
    'ballots': [{
        'ballot_paper_id': 'local.tandridge.bletchingley-nutfield.2024-05-02',
        'label': 'Bletchingley & Nutfield',
        'matched': true,
        'matched_page': '0'
    }, {
        'ballot_paper_id': 'local.tandridge.burstow-horne-outwood.2024-05-02',
        'label': 'Burstow, Horne & Outwood',
        'matched': true,
        'matched_page': '1'
    }, {
        'ballot_paper_id': 'local.tandridge.chaldon.2024-05-02',
        'label': 'Chaldon',
        'matched': true,
        'matched_page': '2'
    }, {
        'ballot_paper_id': 'local.tandridge.dormansland-felbridge.2024-05-02',
        'label': 'Dormansland & Felbridge',
        'matched': true,
        'matched_page': '4'
    }, {
        'ballot_paper_id': 'local.tandridge.godstone.2024-05-02',
        'label': 'Godstone',
        'matched': true,
        'matched_page': '5'
    }, {
        'ballot_paper_id': 'local.tandridge.harestone.2024-05-02',
        'label': 'Harestone',
        'matched': true,
        'matched_page': '6'
    }, {
        'ballot_paper_id': 'local.tandridge.limpsfield.2024-05-02',
        'label': 'Limpsfield',
        'matched': true,
        'matched_page': '7'
    }, {
        'ballot_paper_id': 'local.tandridge.lingfield-crowhurst.2024-05-02',
        'label': 'Lingfield & Crowhurst',
        'matched': true,
        'matched_page': '8'
    }, {
        'ballot_paper_id': 'local.tandridge.oxted-north.2024-05-02',
        'label': 'Oxted North',
        'matched': true,
        'matched_page': '9'
    }, {
        'ballot_paper_id': 'local.tandridge.oxted-south.2024-05-02',
        'label': 'Oxted South',
        'matched': true,
        'matched_page': '10'
    }, {
        'ballot_paper_id': 'local.tandridge.portley-queens-park.2024-05-02',
        'label': 'Portley & Queens Park'
    }, {
        'ballot_paper_id': 'local.tandridge.tatsfield-titsey.2024-05-02',
        'label': 'Tatsfield & Titsey',
        'matched': true,
        'matched_page': '3'
    }, {
        'ballot_paper_id': 'local.tandridge.valley.2024-05-02',
        'label': 'Valley',
        'matched': true,
        'matched_page': '12'
    }, {
        'ballot_paper_id': 'local.tandridge.warlingham-east-chelsham-farleigh.2024-05-02',
        'label': 'Warlingham East & Chelsham & Farleigh',
        'matched': true,
        'matched_page': '13'
    }, {
        'ballot_paper_id': 'local.tandridge.warlingham-west.2024-05-02',
        'label': 'Warlingham West',
        'matched': true,
        'matched_page': '14'
    }, {
        'ballot_paper_id': 'local.tandridge.westway.2024-05-02',
        'label': 'Westway',
        'matched': true,
        'matched_page': '15'
    }, {
        'ballot_paper_id': 'local.tandridge.whyteleafe.2024-05-02',
        'label': 'Whyteleafe',
        'matched': true,
        'matched_page': '16'
    }, {
        'ballot_paper_id': 'local.tandridge.woldingham.2024-05-02',
        'label': 'Woldingham',
        'matched': true,
        'matched_page': '17'
    }]
}

var page_data = document.getElementById("sopn-matcher-index-props")
var data;
if (!page_data) {
    data = dummy_data
} else {
    data = JSON.parse(page_data.textContent)
}

const app = new App({
    target: document.querySelector('#sopn-matcher-index-target'),
    props: data,
})
export default app
