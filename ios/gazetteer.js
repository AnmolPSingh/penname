/**
 * Penname gazetteer — word lists the detector uses to catch a first name or
 * a place that stands on its own ("Thanks to Margaret", "moved to Leeds").
 *
 * Deliberately conservative: a name or place that is also an everyday word
 * is left out, because flagging "May", "Mark", "Bath" or "Reading" in running
 * text would be wrong far more often than right. Those still get caught when
 * they appear as part of a full name or address.
 *
 * Left out on purpose —
 *   names:  April, August, Bill, Chase, Dawn, Dean, Earl, Faith, Frank, Grace,
 *           Guy, Holly, Hope, Hunter, Iris, Ivy, Jack, Joy, June, Mark, Mason,
 *           May, Olive, Pat, Penny, Rich, Rob, Rose, Sue, Summer, Violet, Will
 *   places: Bath, Bury, Deal, Hull, Mobile, Phoenix, Reading, Sale, Wells,
 *           Buffalo, Chester, Jackson, Lincoln, Georgia, Jordan, Victoria
 *
 * No network. No dependencies. Data only.
 */
"use strict";

const FIRST_NAME_LIST = (
  // Women
  "abigail ada adele agnes aisha alice alicia alison amanda amelia amy andrea angela anita ann anna " +
  "anne annette annie aoife barbara beatrice becky bernadette beth bethany betty beverley brenda " +
  "bridget caitlin carla carmen carol carole caroline carolyn catherine cathy catriona charlotte " +
  "cheryl chloe christina christine ciara claire clara claudia colleen constance cynthia daisy " +
  "danielle deborah debra denise diana diane dolores donna dora doreen doris dorothy edith eileen " +
  "elaine eleanor elena elizabeth ella ellen eloise elsie emily emma erica erin esther ethel eva " +
  "evelyn fatima felicity fiona florence frances freya gabrielle gail gemma georgina geraldine " +
  "gillian gloria gwen hannah harriet hazel heather helen helena hilary hilda imogen irene isabel " +
  "isabella isla jacqueline jane janet janice jasmine jean jeanette jemima jennifer jenny jessica " +
  "jill joan joanna joanne jocelyn josephine joyce judith judy julia julie juliet karen kate " +
  "katherine kathleen kathryn katie kayleigh kelly kerry kimberly kirsty laura lauren leah leanne " +
  "lesley lillian linda lisa lois lorna lorraine louise lucy lydia lynda lynn mabel madeleine " +
  "maeve maggie mairead mandy margaret maria marian marie marilyn marion marjorie martha mary " +
  "matilda maureen megan melanie melissa meredith michelle mildred miriam moira molly monica " +
  "muriel nadia nancy naomi natalie natasha niamh nicola nicole nina nora noreen norma olivia " +
  "orla pamela patricia paula pauline peggy philippa phoebe phyllis polly priya rachel rebecca " +
  "rhiannon rita roberta rosalind rosemary rosie ruth sabrina sally samantha sandra sara sarah " +
  "shannon sharon sheila shirley sian sinead siobhan sophia sophie stella stephanie susan susanna " +
  "suzanne sylvia tabitha tamsin tanya teresa theresa tina tracey tracy ursula valerie vanessa " +
  "vera veronica vivian wendy winifred yasmin yvonne zara zoe " +
  // Men
  "aaron abdul adam adrian ahmed aidan alan alastair albert alex alexander alfred ali alistair " +
  "allan andrew angus anthony antony archie arnold arthur barry benjamin bernard bertie bob " +
  "bobby bradley brendan brian bruce callum cameron carl cecil cedric charles charlie christian " +
  "christopher ciaran clifford clive colin connor conor craig cyril damian daniel darren david " +
  "declan dennis derek dermot desmond dominic donald douglas duncan dylan eamon edgar edmund " +
  "edward edwin elliot eric ernest ethan eugene euan ewan fergus finlay francis frederick gareth " +
  "gary gavin geoffrey george gerald gerard gilbert giles gordon graeme graham gregory hamish " +
  "harold harry hassan henry herbert horace howard hugh hugo ian ibrahim isaac ivan jacob jake " +
  "james jamie jason jeffrey jeremy jerome jim jimmy joe joel john johnny jonathan joseph joshua " +
  "julian justin keith kenneth kevin kieran laurence lawrence lee leon leonard leslie lewis liam " +
  "lionel louis luke malcolm marcus martin matthew maurice maxwell michael mohammed montgomery " +
  "murray nathan neil neville nicholas nigel noel norman oliver oscar owen patrick paul percy " +
  "peter philip phillip rajesh ralph raymond reginald rhys richard robert robin rodney roger " +
  "roland ronald rory ross rupert russell ryan samuel sanjay scott seamus sean sebastian shane " +
  "simon stanley stephen steven stuart terence terry theodore thomas timothy toby tony trevor " +
  "tristan vernon victor vincent walter wayne wilfred william zachary"
).split(/\s+/);

const PLACE_LIST = [
  // UK and Ireland
  "aberdeen", "armagh", "bangor", "belfast", "birmingham", "blackpool", "bolton", "bournemouth",
  "bradford", "brighton", "bristol", "cambridge", "canterbury", "cardiff", "carlisle",
  "chelmsford", "cheltenham", "chichester", "colchester", "cork", "coventry", "derby", "doncaster",
  "dublin", "dundee", "durham", "edinburgh", "exeter", "galway", "glasgow", "gloucester",
  "guildford", "hereford", "huddersfield", "inverness", "ipswich", "lancaster", "leeds",
  "leicester", "lichfield", "limerick", "lisburn", "liverpool", "london", "luton", "manchester",
  "middlesbrough", "newcastle", "newport", "northampton", "norwich", "nottingham", "oxford",
  "perth", "peterborough", "plymouth", "portsmouth", "preston", "ripon", "rochdale", "salford",
  "salisbury", "sheffield", "shrewsbury", "southampton", "stirling", "stockport", "sunderland",
  "swansea", "swindon", "truro", "wakefield", "warrington", "watford", "westminster", "winchester",
  "wolverhampton", "worcester", "wrexham", "york",
  // Counties and nations
  "cornwall", "cumbria", "derbyshire", "devon", "dorset", "essex", "hampshire", "hertfordshire",
  "kent", "lancashire", "leicestershire", "lincolnshire", "norfolk", "northumberland",
  "nottinghamshire", "oxfordshire", "shropshire", "somerset", "staffordshire", "suffolk", "surrey",
  "sussex", "warwickshire", "wiltshire", "yorkshire", "england", "scotland", "wales", "ireland",
  // United States and Canada
  "albuquerque", "atlanta", "austin", "baltimore", "boston", "charlotte", "chicago", "cincinnati",
  "cleveland", "columbus", "dallas", "denver", "detroit", "houston", "indianapolis",
  "jacksonville", "memphis", "miami", "milwaukee", "minneapolis", "nashville", "oakland",
  "philadelphia", "pittsburgh", "portland", "sacramento", "seattle", "tucson", "montreal",
  "ottawa", "toronto", "vancouver", "california", "colorado", "connecticut", "florida", "illinois",
  "massachusetts", "michigan", "minnesota", "ohio", "oregon", "pennsylvania", "texas", "virginia",
  // Elsewhere
  "amsterdam", "athens", "auckland", "barcelona", "berlin", "brisbane", "brussels", "copenhagen",
  "geneva", "hamburg", "johannesburg", "lagos", "lisbon", "madrid", "melbourne", "milan",
  "mumbai", "munich", "nairobi", "paris", "prague", "rome", "singapore", "stockholm", "sydney",
  "tokyo", "vienna", "warsaw", "zurich",
  // Two words
  "new york", "los angeles", "san francisco", "san diego", "las vegas", "new orleans",
  "salt lake city", "kansas city", "st albans", "milton keynes", "stoke-on-trent", "east sussex",
  "west sussex", "north yorkshire", "south yorkshire", "west yorkshire", "greater manchester",
  "west midlands", "northern ireland", "isle of wight", "isle of man", "cape town", "hong kong",
  "new delhi", "buenos aires",
];

const PennameGazetteer = {
  firstNames: new Set(FIRST_NAME_LIST),
  places: new Set(PLACE_LIST),
  // Longest first, so "New York" wins over a shorter overlap.
  placeList: PLACE_LIST.slice().sort((a, b) => b.length - a.length),
};

if (typeof module !== "undefined" && module.exports) module.exports = PennameGazetteer;
if (typeof window !== "undefined") window.PennameGazetteer = PennameGazetteer;
