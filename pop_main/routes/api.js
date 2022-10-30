var express = require('express');
var router = express.Router();
const { Deta } = require('deta');
const deta = Deta(process.env.DETA_PROJECT_KEY);
const popDB = deta.Base('PopData');

router.get('/', async (req, res) => {
    res.send("API for Pop EunBin");
});

router.get('/list', async (req, res) => {
    const result = await popDB.fetch({published: true});
    res.send(result.items);
});

router.post('/upload', async (req, res) => {
    const bodyData = req.body;
    try {
        for (let key in bodyData) {
            // check popCount for each key is less than 200 clicks
            if(bodyData[key]<=200){
                await popDB.update({ popCount: popDB.util.increment(bodyData[key]) }, key);
            } 
        }
        res.json({ status: 'success'});
    } catch (error) {
        res.json({ status: 'error', text: error});
    }
});


module.exports = router;
