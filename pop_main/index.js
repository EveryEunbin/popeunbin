const express = require('express');
var bodyParser = require('body-parser');
var cors = require('cors');
require('dotenv').config()

const { Deta } = require('deta')
const deta = Deta(process.env.DETA_PROJECT_KEY);
const popDB = deta.Base('PopData'); // database name

const app = express();

var apiRouter = require('./routes/api');

app.use(cors());
app.use(bodyParser.urlencoded({ extended: false }));
app.use(bodyParser.json());
app.use(express.static('public'))
//setting view engine to ejs
app.set("view engine", "ejs");

app.disable('x-powered-by');

app.get('/', async (req, res) => {
    // const songList = ["thesamebackwardsandforwards.mp3", "thekingsaffection.mp3", "trumerei.mp3",  "fullpower.mp3", "dreamme.mp3", "goodday.mp3"]
    
    res.render('index');
});

app.use('/api', apiRouter);

app.get('/summary', async (req, res) => {
    res.render('summary');
});

app.get('/:key', async (req, res) => {
    const { key } = req.params;
    const result = await popDB.get(key);
    if (result) {
        if (result.published){
            res.render('page', { data: result })
        } else {
            res.redirect('/')
        }
    } else {
        res.redirect('/')
    }

})



app.listen(8000, function () {
    // console.log("Server is running on port 8080 ");
});

// for deta.dev
module.exports = app;
