import App from './App.svelte'

var dummy_data = {
    sopn_pdf: "https://s3.eu-west-2.amazonaws.com/static-candidates.democracyclub.org.uk/media/official_documents/local.tandridge.2024-05-02/2024-04-05T18%3A23%3A03.267470%2B00%3A00/Statement_of_Persons_Nominated_Tandridge_District_2024.pdf",
    'pages': {
        '0': 'local.tandridge.bletchingley-nutfield.2024-05-02',
        '1': 'local.tandridge.burstow-horne-outwood.2024-05-02',
        '2': 'local.tandridge.chaldon.2024-05-02',
        '3': 'local.tandridge.tatsfield-titsey.2024-05-02',
        '4': 'local.tandridge.dormansland-felbridge.2024-05-02',
        '5': 'local.tandridge.godstone.2024-05-02',
        '6': 'local.tandridge.harestone.2024-05-02',
        '7': 'local.tandridge.limpsfield.2024-05-02',
        '8': 'local.tandridge.lingfield-crowhurst.2024-05-02',
        '9': 'local.tandridge.oxted-north.2024-05-02',
        '10': 'local.tandridge.oxted-south.2024-05-02',
        '12': 'local.tandridge.valley.2024-05-02',
        '13': 'local.tandridge.warlingham-east-chelsham-farleigh.2024-05-02',
        '14': 'local.tandridge.warlingham-west.2024-05-02',
        '15': 'local.tandridge.westway.2024-05-02',
        '16': 'local.tandridge.whyteleafe.2024-05-02',
        '17': 'local.tandridge.woldingham.2024-05-02'
    },
    'ballots': [{
        'ballot_paper_id': 'local.tandridge.bletchingley-nutfield.2024-05-02',
        'label': 'Bletchingley & Nutfield',
    }, {
        'ballot_paper_id': 'local.tandridge.burstow-horne-outwood.2024-05-02',
        'label': 'Burstow, Horne & Outwood',
    }, {
        'ballot_paper_id': 'local.tandridge.chaldon.2024-05-02',
        'label': 'Chaldon',
    }, {
        'ballot_paper_id': 'local.tandridge.dormansland-felbridge.2024-05-02',
        'label': 'Dormansland & Felbridge',
    }, {
        'ballot_paper_id': 'local.tandridge.godstone.2024-05-02',
        'label': 'Godstone',
    }, {
        'ballot_paper_id': 'local.tandridge.harestone.2024-05-02',
        'label': 'Harestone',
    }, {
        'ballot_paper_id': 'local.tandridge.limpsfield.2024-05-02',
        'label': 'Limpsfield',
    }, {
        'ballot_paper_id': 'local.tandridge.lingfield-crowhurst.2024-05-02',
        'label': 'Lingfield & Crowhurst',
    }, {
        'ballot_paper_id': 'local.tandridge.oxted-north.2024-05-02',
        'label': 'Oxted North',
    }, {
        'ballot_paper_id': 'local.tandridge.oxted-south.2024-05-02',
        'label': 'Oxted South',
    }, {
        'ballot_paper_id': 'local.tandridge.portley-queens-park.2024-05-02',
        'label': 'Portley & Queens Park'
    }, {
        'ballot_paper_id': 'local.tandridge.tatsfield-titsey.2024-05-02',
        'label': 'Tatsfield & Titsey',
    }, {
        'ballot_paper_id': 'local.tandridge.valley.2024-05-02',
        'label': 'Valley',
    }, {
        'ballot_paper_id': 'local.tandridge.warlingham-east-chelsham-farleigh.2024-05-02',
        'label': 'Warlingham East & Chelsham & Farleigh',
    }, {
        'ballot_paper_id': 'local.tandridge.warlingham-west.2024-05-02',
        'label': 'Warlingham West',
    }, {
        'ballot_paper_id': 'local.tandridge.westway.2024-05-02',
        'label': 'Westway',
    }, {
        'ballot_paper_id': 'local.tandridge.whyteleafe.2024-05-02',
        'label': 'Whyteleafe',
    }, {
        'ballot_paper_id': 'local.tandridge.woldingham.2024-05-02',
        'label': 'Woldingham',
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
