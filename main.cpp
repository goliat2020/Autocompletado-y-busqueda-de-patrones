#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <bits/stdc++.h>
#include <fstream>

namespace py = pybind11;
using namespace std;

set<string> uniqueWords;
string text;

class TrieNode{
public:
    unordered_map<char, TrieNode*> children;
    bool isEndOfWord = false;
};

void read_file(const string& filename){
    ifstream file(filename, ios::in | ios::binary);
    if(!file.is_open()) return;

    // reserve using file size when available
    file.seekg(0, ios::end);
    streamoff sz = file.tellg();
    file.seekg(0, ios::beg);

    text.clear();
    if(sz > 0) text.reserve(static_cast<size_t>(sz));

    // read whole file into text
    text.assign(istreambuf_iterator<char>(file), istreambuf_iterator<char>());
    file.close();

    uniqueWords.clear();
    string word;
    word.reserve(32);

    // single pass: build lowercase alphabetic words and insert to set
    for(unsigned char uch : text){
        if(std::isalpha(uch)){
            word.push_back(static_cast<char>(std::tolower(uch)));
        } else {
            if(!word.empty()){
                uniqueWords.insert(word);
                word.clear();
            }
        }
    }
    if(!word.empty()) uniqueWords.insert(word);
}


vector<int> lps(string P){
    int m = P.size();
    vector<int> v(m, 0);

    int j = 0;
    int i = 1;

    while(i < m){
        if(P[i] == P[j]){
            v[i] = j + 1;
            i++;
            j++;
        }
        else{
            if(j == 0){
                v[i] = 0;
                i++;
            }
            else{
                j = v[j - 1];
            }
        }
    }
    return v;
}

vector<int> kmp(string P, const string& T){
    int n = T.size();
    int m = P.size();
    vector<int> v =lps(P);
    vector<int> match;
    int i = 0;
    int j = 0;
    while(i < n){
        if(T[i] == P[j]){
            i++;
            j++;
        }
        if(j == m){
            match.push_back(i-j);
            j = v[j-1];
        }
        else if (T[i] != P[j]){
            if(j == 0){
                i++;
            }
            else{
                j = v[j-1];
            }
        }
    }
    return match;
}

vector<int> kmp_search(const string &pattern, const string &text){
    return kmp(pattern, text);
}

static TrieNode* root = nullptr;

TrieNode* newNode(){
    return new TrieNode();
}

void createTrie(){
    if(root == nullptr){
        root = newNode();
    }
    TrieNode* curr = root;
    for(auto word : uniqueWords){
        for(auto c : word){
            auto it  = curr->children.find(c);
            if(it == curr->children.end()){
                TrieNode* child = newNode();
                curr->children[c] = child;
                curr = child;
            }
            else{
                curr = it->second;
            }
        }
        curr->isEndOfWord = true;
        curr = root;
    }
}

void trie_collect(TrieNode* node, string &prefix, vector<string> &out, int max_results){
    if(!node) return;
    if((int)out.size() >= max_results) return;
    if(node->isEndOfWord){
        out.push_back(prefix);
        if((int)out.size() >= max_results) return;
    }
    // deterministic order
    vector<char> keys;
    keys.reserve(node->children.size());
    for(auto &p : node->children) keys.push_back(p.first);
    sort(keys.begin(), keys.end());
    for(char k : keys){
        prefix.push_back(k);
        trie_collect(node->children[k], prefix, out, max_results);
        prefix.pop_back();
        if((int)out.size() >= max_results) return;
    }
}

vector<string> autocomplete(const string &prefix, int max_results=10){
    vector<string> out;
    if(root == nullptr || prefix.empty() || max_results <= 0) return out;
    TrieNode* cur = root;
    for(auto c : prefix){
        auto it = cur->children.find(c);
        if(it == cur->children.end()) return out;
        cur = it->second;
    }
    string p = prefix;
    trie_collect(cur, p, out, max_results);
    return out;
}

PYBIND11_MODULE(algorithms, m) {
    m.doc() = "KMP search bindings";
    m.def("read_file", &read_file, "Read entire file into a string");
    m.def("kmp_search", &kmp_search, "Search pattern in text returning start indices");
    m.def("createTrie", &createTrie, "Create a trie from unique words");
    m.def("autocomplete", &autocomplete, py::arg("prefix"), py::arg("max_results")=10,
          "Return up to max_results autocomplete suggestions for prefix");
}