import React, { useState, useEffect, useRef } from 'react';

const Autocomplete = ({ options, value, onChange, placeholder, name }) => {
    const [isOpen, setIsOpen] = useState(false);
    const [searchTerm, setSearchTerm] = useState('');
    const [filteredOptions, setFilteredOptions] = useState([]);
    const [activeIndex, setIndex] = useState(-1);
    const wrapperRef = useRef(null);

    useEffect(() => {
        setSearchTerm(value || '');
    }, [value]);

    useEffect(() => {
        if (searchTerm) {
            const filtered = options.filter(opt =>
                opt.resource.toLowerCase().includes(searchTerm.toLowerCase())
            );
            setFilteredOptions(filtered);
        } else {
            setFilteredOptions(options);
        }
    }, [searchTerm, options]);

    useEffect(() => {
        function handleClickOutside(event) {
            if (wrapperRef.current && !wrapperRef.current.contains(event.target)) {
                setIsOpen(false);
            }
        }
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, [wrapperRef]);

    const handleInputChange = (e) => {
        setSearchTerm(e.target.value);
        setIsOpen(true);
        setIndex(-1);
        // Notify parent of change (even if incomplete)
        onChange({ target: { name, value: e.target.value } });
    };

    const handleSelect = (option) => {
        setSearchTerm(option.resource);
        setIsOpen(false);
        onChange({ target: { name, value: option.resource, selectedOption: option } });
    };

    const handleKeyDown = (e) => {
        if (e.key === 'ArrowDown') {
            setIndex(prev => Math.min(prev + 1, filteredOptions.length - 1));
            setIsOpen(true);
        } else if (e.key === 'ArrowUp') {
            setIndex(prev => Math.max(prev - 1, 0));
        } else if (e.key === 'Enter') {
            if (activeIndex >= 0 && activeIndex < filteredOptions.length) {
                handleSelect(filteredOptions[activeIndex]);
                e.preventDefault();
            }
        } else if (e.key === 'Escape') {
            setIsOpen(false);
        }
    };

    return (
        <div ref={wrapperRef} style={{ position: 'relative', width: '100%' }}>
            <input
                type="text"
                name={name}
                value={searchTerm}
                onChange={handleInputChange}
                onFocus={() => setIsOpen(true)}
                onKeyDown={handleKeyDown}
                placeholder={placeholder}
                autoComplete="off"
                style={{
                    width: '100%',
                    padding: '10px 12px',
                    borderRadius: '6px',
                    border: '1px solid #ddd',
                    fontSize: '14px',
                    outline: 'none',
                    transition: 'border-color 0.2s, box-shadow 0.2s',
                    boxSizing: 'border-box'
                }}
            />
            {isOpen && filteredOptions.length > 0 && (
                <ul style={{
                    position: 'absolute',
                    top: '100%',
                    left: 0,
                    right: 0,
                    backgroundColor: 'white',
                    border: '1px solid #ddd',
                    borderRadius: '6px',
                    marginTop: '4px',
                    padding: 0,
                    margin: '4px 0 0 0',
                    listStyle: 'none',
                    maxHeight: '200px',
                    overflowY: 'auto',
                    zIndex: 1100,
                    boxShadow: '0 4px 12px rgba(0,0,0,0.1)'
                }}>
                    {filteredOptions.map((opt, index) => (
                        <li
                            key={`${opt.resource}-${opt.apiversion}-${index}`}
                            onClick={() => handleSelect(opt)}
                            onMouseEnter={() => setIndex(index)}
                            style={{
                                padding: '10px 12px',
                                cursor: 'pointer',
                                backgroundColor: activeIndex === index ? '#f0f7ff' : 'transparent',
                                borderBottom: '1px solid #f5f5f5',
                                fontSize: '13px',
                                display: 'flex',
                                justifyContent: 'space-between',
                                alignItems: 'center'
                            }}
                        >
                            <span style={{ fontWeight: '500', color: '#333' }}>{opt.resource}</span>
                            <span style={{ fontSize: '11px', color: '#888', backgroundColor: '#f0f0f0', padding: '2px 6px', borderRadius: '4px' }}>
                                {opt.apiversion}
                            </span>
                        </li>
                    ))}
                </ul>
            )}
        </div>
    );
};

export default Autocomplete;
