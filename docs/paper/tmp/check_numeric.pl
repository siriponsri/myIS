use strict;
use warnings;

sub read_text {
    my ($path) = @_;
    open my $fh, '<:raw', $path or die "$path: $!";
    local $/;
    return <$fh>;
}

sub counts {
    my ($text) = @_;
    my %counts;
    $counts{$_}++ for $text =~ /(?<![A-Za-z])\d+(?:[.,]\d+)*(?:%|\\%)?/g;
    return %counts;
}

my $before = read_text($ARGV[0]);
my $after = read_text($ARGV[1]);
if (@ARGV > 2 && $ARGV[2] eq '--ignore-todo-footnote') {
    $before =~ s/^.*TODO:.*\R//mg;
    $before =~ s/(artifact released with the paper\.)1( The responses)/$1$2/;
}

my %before = counts($before);
my %after = counts($after);
my %tokens = map { $_ => 1 } (keys %before, keys %after);
my @diff = grep { ($before{$_} // 0) != ($after{$_} // 0) } sort keys %tokens;

if (@diff) {
    print "$_ before=" . ($before{$_} // 0) . " after=" . ($after{$_} // 0) . "\n" for @diff;
    exit 1;
}

print "NUMERIC_DIFF=0\n";
