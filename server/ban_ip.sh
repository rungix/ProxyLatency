_input=$1
IPT=/sbin/iptables
ETH=eth0

# Die if file not found
[ ! -f "$_input" ] && { echo "$0: File $_input not found."; exit 1; }
$IPT -D INPUT -j droplist
$IPT -D OUTPUT -j droplist
$IPT -D FORWARD -j droplist

$IPT -F droplist
$IPT -X droplist
$IPT -N droplist

egrep -v "^#|^$" $_input | while IFS= read -r ip
do
    echo "Banning IP: " $ip
    $IPT -A droplist -i $ETH -s $ip -j LOG --log-prefix " CDN IP Source Blocked"
    $IPT -A droplist -i $ETH -s $ip -j DROP
    $IPT -A droplist -i $ETH -d $ip -j LOG --log-prefix " CDN IP Dest Blocked"
    $IPT -A droplist -i $ETH -d $ip -j DROP
done < "$_input"

# Drop it 
$IPT -I INPUT -j droplist
$IPT -I OUTPUT -j droplist
$IPT -I FORWARD -j droplist

