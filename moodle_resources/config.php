<?php  // Moodle configuration file

unset($CFG);
global $CFG;
$CFG = new stdClass();

$CFG->dbtype    = 'mysqli';
$CFG->dblibrary = 'native';
$CFG->dbhost    = $_SERVER["DBHOST"];
$CFG->dbname    = $_SERVER["DBNAME"];
$CFG->dbuser    = $_SERVER["DBUSER"];
$CFG->dbpass    = $_SERVER["DBPASS"];
$CFG->prefix    = 'mdl_';
$CFG->dboptions = array (
  'dbpersist' => 0,
  'dbport' => '',
  'dbsocket' => '',
);


$CFG->wwwroot   = $_SERVER["WWWROOT"];
$CFG->dataroot  = '/moodledata/'.$_SERVER["DATAROOT"];
$CFG->admin     = 'admin';

$CFG->directorypermissions = 0777;

if (!file_exists($CFG->dataroot)) {
    mkdir($CFG->dataroot, 0755, true);
}

require_once(dirname(__FILE__) . '/lib/setup.php');

// There is no php closing tag in this file,
// it is intentional because it prevents trailing whitespace problems!
