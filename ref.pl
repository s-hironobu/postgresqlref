#!/usr/bin/perl

$header = "./template/Header";
$footer = "./template/Footer";

$ref_lastmod;
$file;
$key;

#;
#; MAIN
#;
$body = $ARGV[0];
$option = $ARGV[1];
if ($body eq "") {
    print "Usage: ref.pl FILE\n";
    exit;
}

&get_init_data ();

open (FILE, ">$file") || die "Error can't open $file\n";
&make_header ();
&make_body ();
&make_footer ();
close (FILE);

#
# BODY
#
sub make_body {

    open (BODY, $body) || die "Error: can't open body file $body.\n";

    while (<BODY>) {
	chop;
	if ($_ =~ /^\%TITLE/) {
	    $_ =~ s/^\%TITLE\s+//;
	    print FILE "<h2>$_</h2>\n";
	}
	elsif ($_ =~ /%INCLUDE/) {
	    $_ =~ s/^\%INCLUDE\s+//;
	    $_ = "text/part02/" . $_;
	    open (incFILE, $_) || die "Error: can't open file: $_\n";
	    while (<incFILE>) {
		print FILE $_;
	    }
	    close(incFILE);
	}
	elsif ($_ =~ /^\%CHAPTER/) {
	    if ($_ =~ /^\%CHAPTER\(/ ) {
		my(@word) = split (' ', $_);
		$word[0] =~ s/^\%CHAPTER\(//;
		$word[0] =~ s/\)//;

		$_ =~ s/^\%CHAPTER\((.)*\)\s+//;

		print FILE "<div class=\"jumpmenu\"></div><h3 id=\"$word[0]\">$_</h3>\n";
	    }
	    else {
		$_ =~ s/^\%CHAPTER\s+//;
		print FILE "<div class=\"jumpmenu\"></div><h3>$_</h3>\n";
	    }
	}
	elsif ($_ =~ /^\%SECTION/) {
	    if ($_ =~ /^\%SECTION\(/ ) {
		my(@word) = split (' ', $_);
		$word[0] =~ s/^\%SECTION\(//;
		$word[0] =~ s/\)//;

		$_ =~ s/^\%SECTION\((.)*\)\s+//;

		print FILE "<div class=\"jumpmenu\"></div><h4 id=\"$word[0]\">$_</h4>\n";
	    }
	    else {
		$_ =~ s/^\%SECTION\s+//;
		print FILE "<div class=\"jumpmenu\"></div><h4>$_</h4>\n";
	    }
	}
	elsif ($_ =~ /^\%SUBSECTION/) {
	    if ($_ =~ /^\%SUBSECTION\(/ ) {
		my(@word) = split (' ', $_);
		$word[0] =~ s/^\%SUBSECTION\(//;
		$word[0] =~ s/\)//;

		$_ =~ s/^\%SUBSECTION\((.)*\)\s+//;

		print FILE "<div class=\"jumpmenu\"></div><h5 id=\"$word[0]\">$_</h5>\n";
	    }
	    else {
		$_ =~ s/^\%SUBSECTION\s+//;
		print FILE "<div class=\"jumpmenu\"></div><h5>$_</h5>\n";
	    }
	}
	elsif ($_ =~ /^\%COLUMN/) {
	    if ($_ =~ /^\%COLUMN\(/ ) {
		my(@word) = split (' ', $_);
		$word[0] =~ s/^\%COLUMN\(//;
		$word[0] =~ s/\)//;

		$_ =~ s/^\%COLUMN\((.)*\)\s+//;

		print FILE "<div class=\"jumpmenu\"></div><h6 id=\"$word[0]\">$_</h6>\n";
	    }
	    else {
		$_ =~ s/^\%COLUMN\s+//;
		print FILE "<div class=\"jumpmenu\"></div><h6>$_</h6>\n";
	    }
	}
	elsif ($_ =~ /^\%COMMENT/ 
	       || $_ =~ /^%TITLE/ 
	       || $_ =~ /^\%LASTMOD/
	       || $_ =~ /^\%KEY/
	       || $_ =~ /^\%FILE/ ) {
	    ;
	}
	else {
	    print FILE "$_\n";
	}
    }
    close (BODY);
}

#
# HEADER
#
sub make_header {
    open (HEADER, $header) || die "Error: can't open Header file.\n";

    while (<HEADER>) {
	print FILE $_;
    }
    close (HEADER);
}

#
# FOOTER
#
sub make_footer {
    open (FOOTER, $footer) || die "Error: can't open Footer file.\n";

    while (<FOOTER>) {
	chop;
	if ($_ eq "REF_LASTMOD") {
	    print FILE "Last-modified: $ref_lastmod\n";
	}
	else {
	    print FILE "$_\n";
	}
    }
    close (FOOTER);
}

#
#
#
sub get_init_data {
    open (BODY, $body) || die "Error: can't open body file $body.\n";
    while (<BODY>) {
	chop;
	if ($_ =~ /^\%FILE/) {
	    $_ =~ s/^\%FILE\s+//;
	    $_ =~ s/internal/html/;
	    $file = $_;
	}
	elsif ($_ =~ /^\%KEY/) {
	    $_ =~ s/^\%KEY\s+//;
	    $key = $_;
	}
	elsif ($_ =~ /^\%LASTMOD/) {
	    $_ =~ s/^\%LASTMOD\s+//;
	    
	    @datetime = localtime(time);
	    $year = 1900 + $datetime[5];
	    $month = $datetime[4] + 1;
	    $day = $datetime[3];

#	    $ref_lastmod = $_;
	    $ref_lastmod =  "$year-$month-$day";
	}
    }
    close (BODY);
}
