<?php
/**
 * @author Michael Liebler
 * @copyright Copyright (C) 2015 Michael Liebler.
 * @license http://www.gnu.org/copyleft/gpl.html GNU/GPL, see LICENSE.txt


 * @file combarestfull.php

 * Class CombaApiBase
 * Get data from Comba api
 *
Example:
$username = "serviceuser";
$password = "secret";
$host = 'comba-test.critmass.de';
$port = 80;
$combaList = new CombaApiListBroadcasts();

$combaList->setHost($host);
$combaList->setPort($port);

$combaList->setPassword($password);
$combaList->setUser($username);

$combaList->setDatefrom('2015-02-28T12:00');
$combaList->setDateto('2015-03-01T08:00');
$combaList->setState('archived');


$items = $combaList->getItems();

$d = null;
foreach($items as $item) {
    print "\nITEM: \n";
    if (!$d && $item['ressource_ready']) {
        $d = $item;
    }
    foreach($item as $key => $value) {
        print $key . ": " . $value."\n";
    }
}

if ($d) {
    $combaDownload = new CombaApiDownload();

    $combaDownload->setHost($host);
    $combaDownload->setPort($port);

    $combaDownload->setPassword($password);
    $combaDownload->setUser($username);
    $combaDownload->setIdentifier($d['identifier']);
    print "store file to " . '/home/michel/' . $d['identifier'] . ".mp3\n";
    $combaDownload->store('/home/michel/' . $d['identifier'] . '.mp3');
    print "download complete!\n";
}

 */
class CombaApiBase {
	/**
    * saves curl session
    * @var cURL
    */
    protected $ch = null;


    /**
    * saves results
    * @var string
    */
    protected $result = "";

    /**
     * saves params
     * @var array
     */
    protected $params = array();

    /**
     * protocol
     * @var string
     */
    protected $protocol = "http://";

    /**
     * port
     * @var int
     */
    protected $port = 80;

    /**
     * Service user
     * @var string
     */
    protected $user = "serviceuser";

    /**
     * Service users password
     * @var string
     */
    protected $password = "xxxxx";

    /**
     * Url
     * @var string
     */
    protected $url = "/api/v1.0/broadcasts";

    /**
    /**
    * init curl
    */
    public function __construct() {
        $this->ch = curl_init();
    }

    /**
    * Deconstructor
    */
    public function __destruct()
	{
		curl_close($this->ch);
	}

    /**
    * set Comba Host
    */
    public function setHost($host) {
        $this->host = $host;
    }

    /**
     * set Comba Port
     */
    public function setPort($port) {
        $this->port = $port;
    }

    /**
     * set Comba Protocol
     */
    public function setProtocol($protocol) {
        $this->protocol = $protocol;
    }

    /**
     * set service username
     */
    public function setUser($user) {
        $this->user = $user;
    }

    /**
     * set service users password
     */
    public function setPassword($password) {
        $this->password = $password;
    }


    /**
     * Set start date as search param
     * Must be formatted date string: %Y-%m-%dT%H:%M
     * @param string $start
     */
    public function setStart($start) {
        $this->params['start'] = $start;
    }

    /**
     * Set end date as search param
     * Must be formatted date string: %Y-%m-%dT%H:%M
     * @param string $end
     */
    public function setEnd($end) {
        $this->params['end'] = $end;
    }


    /**
     * Set programme id as search param
     *
     * @param string $programme_id
     */
    public function setProgramme_id($programme_id) {
        $this->params['programme_id'] = $programme_id;
    }

    /**
     * Set station_id as search param
     * @param string $station_id
     */
    public function setStation_id($station_id) {
        $this->params['station_id'] = $station_id;
    }


    /**
     * set records identifier as search param
     * @param string $identifier
     */
    public function setIdentifier($identifier) {
        $this->params['identifier'] = $identifier;
    }


    /**
     * Initiate the Request
     */
    protected function _initRequest() {
        $source = $this->protocol . $this->host . ":" . $this->port . $this->url;

        $headers = array(
            'Content-Type: application/json',
        );

        curl_setopt($this->ch, CURLOPT_URL, $source);
        curl_setopt($this->ch, CURLOPT_USERPWD, $this->user . ":" . $this->password);
        curl_setopt($this->ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($this->ch, CURLOPT_HEADER, false);
        curl_setopt($this->ch, CURLOPT_HTTPHEADER, $headers);
        curl_setopt($this->ch, CURLOPT_POST, true);

    }

    protected function _sendRequest() {
        $this->result = curl_exec($this->ch);
    }
}

/**
 * Class CombaApiListBroadcasts
 * Search for programme records
 */

class CombaApiListBroadcasts extends CombaApiBase {

    public $items = array();

    /**
     * Set Limit
     * @param int $limit
     */
    public function setLimit($limit) {
        $this->params['limit'] = $limit;
    }

    /**
     * Set limit start for paging
     * @param int $limitstart
     */
    public function setLimitstart($limitstart) {
        $this->params['limitstart'] = $limitstart;
    }

    /**
     * Set title as search param
     *
     * @param string $title
     */
    public function setTitle($title) {
        $this->params['title'] = $title;
    }


    /**
     * Set state as search param
     * currently 'created' or 'archived'
     * @param string $state
     */
    public function setState($state) {
        $this->params['state'] = $state;
    }

    /**
     * Set rerun as search param
     * Get only reruns
     */
    public function setRerun() {
        $this->params['rerun'] = true;
    }

    /**
     * Set search param search
     * for searching in title, subject or description
     * @param unknown $search
     */
    public function setSearch($search) {
        $this->params['search'] = $search;
    }

    /**
     * Set search param datetimefrom
     * Must be formatted date string: %Y-%m-%dT%H:%M
     * @param string $datefrom
     */
    public function setDatefrom($datefrom) {
        $this->params['datetimefrom'] = $datefrom;
    }

    /**
     * Set search param datetimeto
     * Must be formatted date string: %Y-%m-%dT%H:%M
     * @param string $dateto
     */
    public function setDateto($dateto) {
        $this->params['datetimeto'] = $dateto;
    }

    /**
     * Get only current running programme
     */
    public function setCurrent() {
        $this->params['current'] = true;
    }

    /**
     * Get Data from Server
     * @return number|array
     */
    public function getItems() {
        $this->_initRequest();
        curl_setopt($this->ch, CURLOPT_POSTFIELDS,  json_encode($this->params));
        $this->_sendRequest();
        if (!$this->result) {
            return -1;
        }
        $result_arr = json_decode($this->result, true);

        if (!isset($result_arr['broadcasts'])) {
            return -2;
        }
        $this->items = $result_arr['broadcasts'];

        return $this->items;
    }
}


class CombaApiDownload extends CombaApiBase {


    /**
     * Store Download to file
     * @param string $path
     * @return number|array
     */
    public function store($path) {

        $this->url = "/api/v1.0/broadcasts/download";

        if (!isset( $this->params['identifier'] )
            && !isset( $this->params['start'])
            && !isset( $this->params['end'])
                ) {
            return false;
        }

        $this->_initRequest();

        curl_setopt($this->ch, CURLOPT_POSTFIELDS,  json_encode($this->params));
        $fp = fopen($path, 'w+');
        curl_setopt($this->ch, CURLOPT_FILE, $fp);

        $this->_sendRequest();
        fclose($fp);
        return true;
    }

}